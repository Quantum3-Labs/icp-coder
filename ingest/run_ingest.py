import os
import importlib.util
import inspect

INGEST_DIR = os.path.dirname(__file__)


def find_ingester_classes(module):
    return [obj for name, obj in inspect.getmembers(module, inspect.isclass)
            if name.endswith('Ingester') and hasattr(obj, 'ingest')]

def main():
    for filename in os.listdir(INGEST_DIR):
        if filename.endswith('.py') and filename != os.path.basename(__file__):
            module_name = filename[:-3]
            file_path = os.path.join(INGEST_DIR, filename)
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            for IngesterClass in find_ingester_classes(module):
                print(f"Running {IngesterClass.__name__} from {filename}...")
                ingester = IngesterClass()
                ingester.ingest()

if __name__ == '__main__':
    main() 