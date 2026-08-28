my/tools/ -- scripts you wrote yourself

Nothing here is touched by an upgrade.

To use the framework's configuration or shared helpers, write this
(run from the project root):

    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "scripts/harness"))
    import framework_config

⚠️ You have to write that line yourself because your script is not in scripts/ --
   and it is not in scripts/ precisely so that it survives the next upgrade.
