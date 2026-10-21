import traceback

try:
    from views.fi_accounting import FIAccountingView
    v = FIAccountingView()
    print("FIAccountingView instantiated successfully!")
except Exception as e:
    print("Error instantiating FIAccountingView:")
    traceback.print_exc()
