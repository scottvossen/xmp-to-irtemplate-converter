import glob
import re
import os
import shutil
import uuid

def parse_xmp(xmp, fname):

    final_string = ''

    open_flag = False
    for line in xmp.splitlines():

        x = re.match(".*<crs:ToneCurvePV2012.*", line)
        if x:
            line = re.sub(r".*crs:(\w*)", r"\1 = {", line)
            line = re.sub(r">", r"", line)
            open_flag = True

        linebefore = line
        line = re.sub(r".*<rdf:li>(\d*),\s*(\d*).*", r"\1,\n\2,", line)
        lineafter = line

        line = re.sub(r"\+", "", line)
        line = re.sub(r"^\s*crs\:", "", line)
        line = re.sub(r'\"(-*\d*\.*\d*)\"', r"\1", line)

        #all the remaining lines that begin with a \s*< in them are garbage
        y =  re.match("^\s+", line)
        z = re.match("^\s*<", line)
        a = re.match("^\w*=\n", line)
        b = re.match(".*>$", line)
        c = re.match("\w*=$", line)
        if not y and not z and not a and not b and not c:
            final_string = final_string + "\n" + line

    final_string = re.sub(r"\n\s*\n", "\n", final_string)    
    final_string = re.sub(r"(\d+),\n(\D)", r"\1,\n}\n\2", final_string)    
    final_string = final_string + "\n}"
    final_string = re.sub(r"(\S)=(\S)", r"\1 = \2", final_string)    
    final_string = re.sub(r"(\d*,)\n", r"\1", final_string)    
    final_string = re.sub(r"{\s*\n", r"{", final_string) 

    xmp_dict = {}
    pattern = "(\w*) = (\"*-*\w*\.*\w+[ \w*]*\"*)"
    my_list = re.findall(pattern, final_string, re.MULTILINE)
    xmp_dict = {a:b for a,b in my_list}

    xmp_dict_list = {}
    pattern = "(\w*) = ({[\d*,*]*})"
    my_list = re.findall(pattern, final_string, re.MULTILINE)
    xmp_dict_list = {a:b for a,b in my_list}

    lrtemplate_dict = {**xmp_dict, **xmp_dict_list}

    rem_list = [
        'HasSettings',
        'IncrementalTemperature', 
        'IncrementalTint',
        'PresetType', 
        'SupportsAmount', 
        'SupportsColor', 
        'SupportsHighDynamicRange', 
        'SupportsMonochrome', 
        'SupportsNormalDynamicRange', 
        'SupportsOutputReferred', 
        'SupportsSceneReferred', 
        'Texture',
        'UUID', 
        'Version'
    ]
    
    for key in rem_list:
        try:
            lrtemplate_dict.pop(key)
        except:
            # value not present in dict
            do = "nothing"

    lrtemplate_dict = dict(sorted(lrtemplate_dict.items()))
    lrtemplate_dict["ProcessVersion"] = '"6.7"' 

    lrtemplate_string = '''s = {
    id = "@uuid1@",
    internalName = "@filename@",
    title = "@filename@",
    type = "Develop",
    value = {
        settings = {
'''
    lrtemplate_string = re.sub(r"@filename@", fname, lrtemplate_string)
    lrtemplate_string = re.sub(r"@uuid1@", str(uuid.uuid4()), lrtemplate_string)

    for k, v in lrtemplate_dict.items():
        if re.match("{", v):
            lrtemplate_string = lrtemplate_string + "\t\t\t" + k + " = {\n"
            v = re.sub(r"[{*}*]", "", v) 
            v = re.sub(r",$", "", v) 
            v_list = v.split(",")
            map_object = map(int, v_list)
            list_of_integers = list(map_object)
            for val in list_of_integers:
                lrtemplate_string = lrtemplate_string + "\t\t\t\t" + str(val) + ",\n"
            lrtemplate_string = lrtemplate_string + "\t\t\t},\n"
        else:
            lrtemplate_string = lrtemplate_string + "\t\t\t" + k + " = " + str(v) + ",\n"
    lrtemplate_string = lrtemplate_string +  \
'''		},
        uuid = "@uuid2@",
    },
    version = 0,
}'''

    lrtemplate_string = re.sub(r"\"False\"", "false", lrtemplate_string) 
    lrtemplate_string = re.sub(r"\"True\"", "true", lrtemplate_string)
    lrtemplate_string = re.sub(r"@uuid2@", str(uuid.uuid4()), lrtemplate_string)
    
    return lrtemplate_string

root_dir = 'lrdata/'
for filepath in glob.iglob(root_dir + '**/*.xmp', recursive=True):
    fname = filepath.split("/")[-1].split(".xmp")[0]

    save_file_path = re.sub(r"\.xmp", ".lrtemplate", filepath) 
    save_file_path = re.sub(r"lrdata", "lrtemplate", save_file_path)
    
    save_folder = re.sub(r"\/" + fname + "\.lrtemplate", "", save_file_path)
    sub_folder_name = save_folder.split("/")[-1]
    save_folder = re.sub(r"\/" + sub_folder_name, "", save_folder)
    save_file_path = re.sub(r"\/" + sub_folder_name, "", save_file_path)
    
    f = open(filepath, "r")
    xmp = f.read()   
    
    lrtemplate_string = parse_xmp(xmp, fname)

    if not os.path.isdir(save_folder):
        os.makedirs(save_folder)

    final_text_file = open(save_file_path, "w")
    n = final_text_file.write(lrtemplate_string)
    final_text_file.close()