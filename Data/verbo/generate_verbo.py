import os
dir_path = os.path.dirname(os.path.realpath(__file__))
import tqdm
import random
from shutil import copyfile
from collections import Counter
import xml.etree.ElementTree as ET
from PIL import ImageFile, Image
ImageFile.LOAD_TRUNCATED_IMAGES = True

targets = ["CheckBox","Button","Chronometer","RadioButton","RatingBar","SeekBar","Spinner","ToggleButton","ProgressBar","Switch","ImageButton"]
IOU_THRESHOLD = 0.5

def parseXML(xmlfile): 
    result = []
    tree = ET.parse(xmlfile) 
    root = tree.getroot()
    items = root.findall('node')
    while len(items)>0:
        child = items.pop(0)
        try:
            c = child.get('class').rsplit('.',1)[1]
        except:
            continue
        bounds = [int(x) for x in child.get('bounds')[1:-1].replace('][',',').split(',')]
        # check valid bounds
        if any(b<0 for b in bounds) or bounds[2]<bounds[0] and bounds[3]<bounds[1]:
            continue
        # check component type
        if c in targets:
            result.append((c,bounds))
        
        items += child.findall('node')
    return result

def pascal_xml(img_name,img_width, img_height,img_depth,objects):
    # img = Image.open(imgfile)
    # img_name = imgfile.split('/')[-4]+imgfile.split('/')[-1]
    # img_width, img_height = img.size
    # img_depth = 3

    root = ET.Element("annotation")
    ET.SubElement(root, "folder").text = "VOC2012"
    ET.SubElement(root, "filename").text = img_name
    source = ET.SubElement(root, "source")
    ET.SubElement(source, "database").text = "The VOC2007 Database"
    ET.SubElement(source, "annotation").text = "PASCAL VOC2007"
    ET.SubElement(source, "image").text = " "
    size = ET.SubElement(root, "size")
    ET.SubElement(size, "width").text = str(img_width)
    ET.SubElement(size, "height").text = str(img_height)
    ET.SubElement(size, "depth").text = str(img_depth)
    ET.SubElement(root, "segmented").text = "0"
    for o in objects:
        img_type = o[0]
        xmin,ymin,xmax,ymax = o[1]

        ob = ET.SubElement(root, "object")
        ET.SubElement(ob, "name").text = img_type
        ET.SubElement(ob, "pose").text = " "
        ET.SubElement(ob, "truncated").text = "0"
        ET.SubElement(ob, "difficult").text = "0"
        bnd = ET.SubElement(ob, "bndbox")
        ET.SubElement(bnd, "xmin").text = str(xmin)
        ET.SubElement(bnd, "ymin").text = str(ymin)
        ET.SubElement(bnd, "xmax").text = str(xmax)
        ET.SubElement(bnd, "ymax").text = str(ymax)
    tree = ET.ElementTree(root)
    return tree

def generate_pascal():
    if not os.path.isdir("./Annotations/"):
        os.mkdir("./Annotations/")
    if not os.path.isdir("./JPEGImages/"):
        os.mkdir("./JPEGImages/")
    if not os.path.isdir("./ImageSets/"):
        os.mkdir("./ImageSets/")
        os.mkdir("./ImageSets/Main/")
    c = []
    json_dir = dir_path+"/5k_data/train_data_path.json"
    f = open(json_dir,'r')
    data = eval(f.read())
    f.close()
    for v,apps in data.items():
        for a in tqdm.tqdm(apps):
            for i in apps[a]:
                xmlfrom_ = dir_path+"/"+v+"/"+a+"/stoat_fsm_output/ui/"+i
                imgfrom_ = dir_path+"/"+v+"/"+a+"/stoat_fsm_output/ui/"+i.replace('xml','png')
                if not (os.path.exists(xmlfrom_) and os.path.exists(imgfrom_)):
                    continue
                # Annotations
                ob = parseXML(xmlfrom_)
                c += [x[0] for x in ob]
                if len(ob) == 0: continue
                img = Image.open(imgfrom_)
                img_name = imgfrom_.split('/')[-4]+imgfrom_.split('/')[-1]
                img_width, img_height = img.size
                img_depth = 3
                tree = pascal_xml(img_name,img_width, img_height,img_depth,ob)
                tree.write("./Annotations/"+a+"_"+i)
                # JPEGImages
                to = "./JPEGImages/"+a+"_"+i.replace('xml','png')
                copyfile(imgfrom_,to)
                # Main
                f = open("./ImageSets/Main/train.txt","a")
                f.write(a+"_"+i.replace('.xml','')+'\n')
                f.close()
    print(Counter(c))
    return Counter(c)

def get_iou(bb1, bb2):
    """
    Calculate the Intersection over Union (IoU) of two bounding boxes.
    Parameters
    ----------
    bb1 : list
        List: [x1, y1, x2, y2]
        The (x1, y1) position is at the top left corner,
        the (x2, y2) position is at the bottom right corner
    bb2 : list
        List: [x1, y1, x2, y2]
        The (x, y) position is at the top left corner,
        the (x2, y2) position is at the bottom right corner
    Returns
    -------
    float
        in [0, 1]
    """
    assert bb1[0] < bb1[2]
    assert bb1[1] < bb1[3]
    assert bb2[0] < bb2[2]
    assert bb2[1] < bb2[3]
    # determine the coordinates of the intersection rectangle
    x_left = max(bb1[0], bb2[0])
    y_top = max(bb1[1], bb2[1])
    x_right = min(bb1[2], bb2[2])
    y_bottom = min(bb1[3], bb2[3])
    if x_right < x_left or y_bottom < y_top:
        return 0.0
    # The intersection of two axis-aligned bounding boxes is always an
    # axis-aligned bounding box
    intersection_area = (x_right - x_left) * (y_bottom - y_top)
    # compute the area of both AABBs
    bb1_area = (bb1[2] - bb1[0]) * (bb1[3] - bb1[1])
    bb2_area = (bb2[2] - bb2[0]) * (bb2[3] - bb2[1])
    # compute the intersection over union by taking the intersection
    # area and dividing it by the sum of prediction + ground-truth
    # areas - the interesection area
    iou = intersection_area / float(bb1_area + bb2_area - intersection_area)
    assert iou >= 0.0
    assert iou <= 1.0
    return iou

def apply_augmentation(class_,number_of_augmentation):
    # get all images and widgets candidates
    imgs = os.listdir('./verbo/JPEGImages/')
    if os.path.exists('./verbo/JPEGImages/.DS_Store'): imgs.remove('.DS_Store')
    widgets = os.listdir('/Users/mac/Documents/Python/Data/Gallery_D.C./all_widgets')
    if os.path.exists('/Users/mac/Documents/Python/Data/Gallery_D.C./all_widgets/.DS_Store'): 
        widgets.remove('.DS_Store')
    widgets = [x for x in widgets if x.split('-')[0] == class_]
    # combine widgets candidates with images
    while number_of_augmentation > 0:
        if number_of_augmentation % 50 == 0:
            print("$$$$$$ ",number_of_augmentation," $$$$$$")
        # find a random images with pre_defined widgets and a random widgets
        name = random.choice(imgs)
        img = Image.open('./verbo/JPEGImages/'+name)
        ###### TODO: read from annotations, avoid double augmentation
        if os.path.exists("/Volumes/Macintosh HD/Users/charlie/Documents/verbo1/"+name.rsplit('_',2)[0]+"/stoat_fsm_output/ui/"+name.split('_',2)[-1].replace('png','xml')):
            pre_widgets = parseXML("/Volumes/Macintosh HD/Users/charlie/Documents/verbo1/"+name.rsplit('_',2)[0]+"/stoat_fsm_output/ui/"+name.split('_',2)[-1].replace('png','xml'))
        elif os.path.exists("/Volumes/Macintosh HD/Users/charlie/Documents/verbo2/"+name.rsplit('_',2)[0]+"/stoat_fsm_output/ui/"+name.split('_',2)[-1].replace('png','xml')):
            pre_widgets = parseXML("/Volumes/Macintosh HD/Users/charlie/Documents/verbo2/"+name.rsplit('_',2)[0]+"/stoat_fsm_output/ui/"+name.split('_',2)[-1].replace('png','xml'))
        elif os.path.exists("/Volumes/Macintosh HD/Users/charlie/Documents/verbo3/"+name.rsplit('_',2)[0]+"/stoat_fsm_output/ui/"+name.split('_',2)[-1].replace('png','xml')):
            pre_widgets = parseXML("/Volumes/Macintosh HD/Users/charlie/Documents/verbo3/"+name.rsplit('_',2)[0]+"/stoat_fsm_output/ui/"+name.split('_',2)[-1].replace('png','xml'))
        else:
            continue
        # pre_widgets = [x[1] for x in pre_widgets]
        widget = Image.open('/Users/mac/Documents/Python/Data/Gallery_D.C./all_widgets/'+random.choice(widgets))
        # find free space for new widget
        width,height = img.size
        wid_width, wid_height = widget.size
        if wid_width <=0 or wid_height<= 0 or width-wid_width<0 or height-wid_height<0:
            continue
        try_ = 0
        while try_<20:
            try_ += 1
            ###### TODO: ValueError: empty range for randrange() (0,-555, -555)
            rand_x = random.randint(0,width-wid_width)
            rand_y = random.randint(0,height-wid_height)
            bounds = [rand_x, rand_y, rand_x+wid_width, rand_y+wid_height]
            IOUs = [get_iou(x[1],bounds) for x in pre_widgets]
            if all(x < IOU_THRESHOLD for x in IOUs):
                img.paste(widget,(rand_x,rand_y))
                pre_widgets.append((class_,bounds))
                # Annotations
                img_name = './verbo/JPEGImages/'+name
                tree = pascal_xml(img_name,width, height,3,pre_widgets) 
                tree.write("./Annotations/"+name.replace('png','xml'))
                # JPEGImages
                to = "./JPEGImages/"+name
                img.save(to)
                number_of_augmentation -= 1
                break

def balance(counts):
    THRESHOLD = 30000
    for class_, number in counts.most_common():
        print(class_+' processing....')
        if number<THRESHOLD:
            apply_augmentation(class_,THRESHOLD-number)



if __name__ == '__main__': 
    # # generate pascal format dataset
    counts = generate_pascal()
    counts = Counter({'ImageButton': 71879, 'Button': 63956, 'CheckBox': 8787, 'ProgressBar': 6314, 'RadioButton': 5880, 'Spinner': 3198, 'ToggleButton': 2551, 'SeekBar': 2239, 'Switch': 1578, 'RatingBar': 1160, 'Chronometer': 25})
