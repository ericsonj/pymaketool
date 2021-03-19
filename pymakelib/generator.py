from pkg_resources import resource_filename

def init_template(outfolder, keyvalues):
    keyfile = resource_filename("pymakelib.resources.templates", "temp.txt")
