from app import app


@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Post=Post)