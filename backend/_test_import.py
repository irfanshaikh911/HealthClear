try:
    from app.main import app
    print("OK - all imports passed")
    for r in app.routes:
        if hasattr(r, "methods"):
            print(f"  {r.path}  {r.methods}")
except Exception as e:
    import traceback
    traceback.print_exc()
