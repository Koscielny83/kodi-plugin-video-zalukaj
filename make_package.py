import re
import shutil
import sys

package = "plugin.video.zalukaj"


def make_package(ver):
    shutil.make_archive("dist/{}-{}".format(package, ver), 'zip', base_dir=package)


if __name__ == "__main__":
    version = sys.argv[1]

    if bool(re.search("^[0-9]+.[0-9]+.[0-9]$", version)):
        make_package(version)
        exit(0)

    exit(1)
