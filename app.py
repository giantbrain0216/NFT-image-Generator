import eel
import wx
import os
import json
from PIL import Image
import random
import shutil
import base64

eel.init('web')


@eel.expose
def browseFolder(self, message):
    defaultPath = os.getcwd()
    app = wx.App(None)
    dlg = wx.DirDialog(
        self, message=message,
        defaultPath=defaultPath,
        style=wx.STAY_ON_TOP)
    # Show the dialog and retrieve the user response.
    if dlg.ShowModal() == wx.ID_OK:
        # load directory
        path = dlg.GetPath()
    else:
        path = ''
    # Destroy the dialog.
    dlg.Destroy()
    if path != '':
        return loadResource(path)
    return "path error!"


def loadResource(path):
    resList = []
    entries = os.scandir(path)
    i: int = 0
    for entry in entries:
        if(entry.is_dir()):
            resList += [{'id': entry.name, 'parent': "#",
                         'text': entry.name, 'icon': "jstree-folder"}]
            entry2 = os.scandir(entry.path)
            for entry3 in entry2:
                i = int(i) + 1
                index = entry3.name.find('.png')
                resList += [{'id': entry3.name[:index] + str(
                    i) + entry3.name[index:], 'parent': entry.name, 'text': entry3.name, 'icon': "jstree-file", 'path': entry3.path}]
    return json.dumps(resList)


@eel.expose
def combineImages(data):
    d = json.loads(data)
    result = generateImages(d)
    return result


def generateImages(d):
    all_images = []
    number = int(d['number'])
    projectName = d['projectName']
    uploadURL = d['uploadURL']

    if(os.path.isdir('results') != True):
        os.makedirs('results')
    else:
        shutil.rmtree('results')
        os.makedirs('results')

    if(os.path.isdir('metadata') != True):
        os.makedirs('metadata')
    else:
        shutil.rmtree('metadata')
        os.makedirs('metadata')

    for it in range(number):
        new_image = {}
        preparedData = prepareData(d)
        img = 'EMPTY'

        for i in range(len(preparedData)):
            if(i == 0):
                img = Image.alpha_composite(Image.open(preparedData[i]['path']).convert(
                    'RGBA'), Image.open(preparedData[i+1]['path']).convert('RGBA'))
            else:
                if(i < (len(preparedData)-1)):
                    img = Image.alpha_composite(img, Image.open(
                        preparedData[i+1]['path']).convert('RGBA'))

            new_image[preparedData[i]['parent'].replace(preparedData[i]['parent'].split('_')[0] + '_', '')] = preparedData[i]['path'].split(
                '\\')[-1].replace('.png', '').replace(preparedData[i]['path'], '')

        new_image['tokenId'] = str(it)
        rgbImg = img.convert('RGB')
        all_images.append(new_image)

        rgbImg.save("./results/" + new_image['tokenId'] + ".png")

    METADATA_FILE_NAME = 'all-traits.json'
    with open('./metadata/' + METADATA_FILE_NAME, 'w') as outfile:
        json.dump(all_images, outfile, indent=4)

    f = open('./metadata/all-traits.json')
    allTraits = json.load(f)
    for i in allTraits:
        tokenId = i['tokenId']
        token = {
            "image": uploadURL + '/' + tokenId + ".png",
            "tokenId": tokenId,
            "name": projectName + ' ' + str(tokenId),
            "attributes": []
        }
        for key in i.keys():
            token['attributes'].append(getAttribute(key, i[key]))

        with open('./metadata/' + tokenId, 'w') as outfile:
            json.dump(token, outfile, indent=4)

    return 'success'


def getAttribute(key, value):
    return {
        "trait_type": key,
        "value": value
    }


def prepareData(data):
    datums = []
    for i in data["unwantImages"]:
        if(i["group"] != '#'):
            stop = len(i["children"]) - 1
            start = 0
            randIndex = random.randint(start, stop)
            datums.append({'parent': i["children"][randIndex]["original"]
                          ["parent"], 'path': i["children"][randIndex]["original"]["path"]})

    for i in data["importantImages"]:
        if(i["group"] != '#'):
            datums.append({'parent': i["children"][0]["original"]
                          ["parent"], 'path': i["children"][0]["original"]["path"]})
    unique = {each['parent']: each for each in datums}.values()
    result = json.loads(json.dumps(list(unique)))
    result.sort(key=lambda x: x["parent"])
    return result

@eel.expose
def getImgSrc(path):
    f =  open(path, 'rb')
    data = f.read()
    data = base64.b64encode(data).decode("utf-8")
    return data

    
eel.start('index.html')
