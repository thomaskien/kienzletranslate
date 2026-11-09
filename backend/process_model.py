"""GPU process boundary: stopping the child releases its entire CUDA context."""
import multiprocessing
import os
import subprocess


class ModelOperationError(RuntimeError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def gpu_free_mib():
    # nvidia-smi does not initialize CUDA in the persistent HTTP process.
    device = os.environ.get('CUDA_VISIBLE_DEVICES', '0').split(',')[0]
    if not device:
        raise ModelOperationError('gpu_unavailable')
    try:
        value = subprocess.check_output(
            ['nvidia-smi', '-i', device, '--query-gpu=memory.free', '--format=csv,noheader,nounits'],
            text=True, timeout=5, stderr=subprocess.DEVNULL)
        return int(value.strip().splitlines()[0])
    except (OSError, ValueError, subprocess.SubprocessError):
        raise ModelOperationError('gpu_unavailable') from None


def _gpu_worker(connection, path):
    # Spawn, never fork an initialized CUDA runtime. Audio stays in anonymous IPC.
    from .model import Model
    model = Model(path)
    try:
        while True:
            command, arguments = connection.recv()
            if command == 'stop':
                break
            try:
                result = getattr(model, command)(*arguments)
                connection.send({'ok': True, 'result': result})
            except Exception as exc:
                code = 'gpu_memory' if 'OutOfMemory' in type(exc).__name__ else 'model_error'
                connection.send({'ok': False, 'code': code})
                break  # discard failed CUDA context as well
    except (EOFError, BrokenPipeError):
        pass
    finally:
        connection.close()


class ProcessModel:
    def __init__(self, path, minimum_free_mib=8192, timeout=180, memory_reader=gpu_free_mib):
        self.path, self.minimum_free_mib = path, minimum_free_mib
        self.timeout, self.memory_reader = timeout, memory_reader
        self.state, self.error, self.error_code = 'unloaded', None, None
        self.process = self.connection = None

    def _exchange(self, command, *arguments):
        try:
            self.connection.send((command, arguments))
            if not self.connection.poll(self.timeout):
                raise ModelOperationError('model_timeout')
            response = self.connection.recv()
            if not response['ok']:
                raise ModelOperationError(response['code'])
            return response['result']
        except (EOFError, BrokenPipeError, OSError):
            raise ModelOperationError('model_error') from None

    def load(self):
        if self.state == 'ready' and self.process and self.process.is_alive():
            return
        self.unload()
        self.state = 'loading'
        try:
            if self.memory_reader() < self.minimum_free_mib:
                raise ModelOperationError('gpu_memory')
            context = multiprocessing.get_context('spawn')
            self.connection, child = context.Pipe()
            self.process = context.Process(target=_gpu_worker, args=(child, self.path), daemon=True)
            self.process.start()
            child.close()
            self._exchange('load')
            self.state = 'ready'
        except Exception as exc:
            self.unload()
            self.state, self.error_code = 'error', getattr(exc, 'code', 'model_error')
            self.error = 'GPU-Speicher belegt.' if self.error_code == 'gpu_memory' else 'Modell konnte nicht geladen werden.'
            raise

    def unload(self):
        self.state = 'unloading'
        if self.process:
            if self.process.is_alive():
                try:
                    self.connection.send(('stop', ()))
                except (OSError, EOFError):
                    pass
                self.process.join(3)
                if self.process.is_alive():
                    self.process.terminate()
                    self.process.join(3)
                if self.process.is_alive():
                    self.process.kill()
                    self.process.join(3)
            self.process.close()
        if self.connection:
            self.connection.close()
        self.process = self.connection = None
        self.state, self.error, self.error_code = 'unloaded', None, None

    def translate(self, *args):
        self.load()
        try:
            return self._exchange('translate', *args)
        except Exception as exc:
            self.unload()
            self.state, self.error_code = 'error', getattr(exc, 'code', 'model_error')
            self.error = 'Modellverarbeitung fehlgeschlagen.'
            raise
