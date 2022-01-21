import os
import sys
import webbrowser
from http.server import HTTPServer, CGIHTTPRequestHandler

def main():

    # to make a new update that requires new packages: append the name of the package in the list and try to import it
    new_packages = ["GitPython"]
    try:
        import git
    except:
        for package in new_packages:
            os.system("\"{}\\python.exe\" -m pip install {}".format(os.path.join(os.path.dirname(os.path.abspath(__file__)), "Python39"), package))

    os.environ['GIT_PYTHON_GIT_EXECUTABLE'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "PortableGit", "bin", "git.exe")
    os.environ['PYTHONUTF8'] = "1"
    path = os.path.dirname(os.path.abspath(__file__))

    try:
        from git import Repo
        repo = Repo('{}'.format(path))
        current = repo.head.commit
        repo.config_writer().set_value("user", "name", "myusername").release()
        repo.config_writer().set_value("user", "email", "myemail").release()
        repo.config_writer().set_value("core", "fileMode", "false").release()
        repo.config_writer().set_value("core", "autocrlf", "true").release()
        repo.git.pull()
        if current != repo.head.commit:
            print("Julgamento was updated. Please, open it again.")
            sys.exit()
    except Exception as e:
        print("Warning (Git): {}".format(e))

    if not os.path.isfile(os.path.join(os.path.dirname(os.path.abspath(__file__)), "prod.db")):
        os.system("\"{}\\python.exe\" once.py".format(os.path.join(os.path.dirname(os.path.abspath(__file__)), "Python39")))    
    
    print("\n=== JULGAMENTO ===\n\n>>> Open 'http://localhost:5050' on your browser to access Julgamento locally.\n")
    webbrowser.open('http://localhost:5050')
    os.system("\"{}\\python.exe\" app.py prod".format(os.path.join(os.path.dirname(os.path.abspath(__file__)), "Python39")))
    
main()