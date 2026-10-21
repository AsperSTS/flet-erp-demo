import traceback

try:
    from views.dashboard import DashboardView
    d = DashboardView()
    print("Dashboard instantiated successfully!")
except Exception as e:
    print("Error instantiating Dashboard:")
    traceback.print_exc()
