from typing import Union, Callable
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
import traceback
from services.budget_service import BudgetService

class DataLoaderWorker(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, task_target: Union[str, Callable], *args, **kwargs):
        super().__init__()
        self.task_target = task_target
        self.args = args
        self.kwargs = kwargs

    @pyqtSlot()
    def run(self):
        try:
            with BudgetService() as local_service:
                result = None
                
                if isinstance(self.task_target, str):
                    if not hasattr(local_service, self.task_target):
                        raise AttributeError(f"Method {self.task_target} not found")
                    method = getattr(local_service, self.task_target)
                    result = method(*self.args, **self.kwargs)
                    
                elif callable(self.task_target):
                    result = self.task_target(local_service, *self.args, **self.kwargs)
                else:
                    raise TypeError("task_target must be a method name (str) or callable")

                self.finished.emit(result)

        except Exception as e:
            print(traceback.format_exc())
            self.error.emit(str(e))