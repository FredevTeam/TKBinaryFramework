# -*- coding: UTF-8 -*-import os
import sys
import json
import glob
import datetime
import oss2
import shutil
import subprocess


'''
代码提交脚本 
    1. 此脚本借助了 carthage，需要安装此工具 brew install carthage 
    2. 此脚本使用了阿里云进行二进制存储，可以替换为自己的存储方 
'''

key = 'XXXXX'
secret = 'xxxxx'
url = 'http://oss-cn-beijing.aliyuncs.com'
bucketname = 'binaryframework'
download_host = 'https://binaryframework.oss-cn-beijing.aliyuncs.com/'
# 存放源码 podspec 文件库
source_pod_spec = 'https://github.com/zhuamaodeyu/LibSpec.git,https://github.com/CocoaPods/Specs.git'
# 存放二进制 podspec 文件库
binary_pod_spec = 'https://github.com/zhuamaodeyu/LibSpec.git,https://github.com/CocoaPods/Specs.git'


def check_has_podspec_file():
    pod_list = glob.glob(os.getcwd() + '/*.podspec')
    if len(pod_list) > 0:
        return  pod_list
    return  None

def check_Carthage():
    if not os.path.isfile(os.getcwd() + '/Cartfile'):
        os.system('touch Cartfile')

def reset_zip_dir():
    if not os.path.exists('zip/'):
        os.mkdir('zip')
    else:
        shutil.rmtree('zip')
        os.mkdir('zip')

def reset_workspace():
    if os.path.isdir(os.getcwd() + '/Carthage'):
        shutil.rmtree(os.getcwd() + '/Carthage')
        os.mkdir(os.getcwd() + '/Carthage')
        pass
    list = glob.glob(os.getcwd() + '/*.podspec.json')
    for l in list:
        os.remove(l)
    reset_zip_dir()


def carthage_build():
    p = subprocess.run('carthage update --platform ios  --verbose',  shell=True)
    pp = subprocess.run('carthage build --no-skip-current --platform ios  --verbose',shell=True)
    if p.returncode == 0 and pp.returncode == 0:
        return  True
    return  False

def pod_install(path):
    os.chdir(path)
    s =  subprocess.run('pod update --no-repo-update', shell=True,encoding="utf-8")
    if s.returncode < 0:
        fail_work(True)
    os.chdir(os.path.abspath(os.path.dirname(os.getcwd())))

def check_profile():
    if os.path.exists(os.getcwd() + '/Podfile'):
        return os.path.join(os.getcwd(), 'Podfile')
    if os.path.exists(os.getcwd() + '/Example'):
        if os.path.exists(os.getcwd() + '/Example/Podfile'):
            return os.path.join(os.getcwd(), 'Example/Podfile')
    return  None

def update_profile(path):
    shell_text = "grep -c \"{0}\" {1}".format('share_schemes_for_development_pods',path)
    exists = subprocess.run(shell_text,shell=True,stdout=subprocess.PIPE,encoding='UTF-8').stdout.replace("\n", "")
    if int(exists) > 0:
        return
    
    if os.path.exists(path):
        with open(path,'a') as file:
            text = "install! 'cocoapods',:share_schemes_for_development_pods => true"
            file.write('\n')
            file.write(text)

def transition_spec_to_json(path):
    dirname = os.path.dirname(path)
    # basename = os.path.splitext(os.path.basename(path))
    pod_json_files = glob.glob(dirname + '/*.json')   
    for f in pod_json_files:
        os.remove(f)
    s = subprocess.run('pod ipc spec ' + path + ' >> ' + path + '.json',shell=True,stdout=subprocess.PIPE,encoding="utf-8")  
    # bin_file = os.path.join(dirname, '{0}Bin{1}{2}'.format(basename[0],basename[1],'.json'))
    # ss = subprocess.run('pod ipc spec ' + path + ' >> ' + bin_file ,shell=True,stdout=subprocess.PIPE,encoding="utf-8")
    # or ss.returncode < 0
    if s.returncode < 0 :
        print(s.stderr)
        fail_work(True)
    # subprocess.run('echo {0}> .gitignore'.format(basename + '.json'),shell=True)





def get_version_and_name(path):
    with open(path) as json_file:
        json_data = json.load(json_file)
        if ("version" in json_data):
            return (json_data['name'],json_data['version'])
    return None

def update_gitignore():
    strings = ['.DS_Store','build/','/zip','DerivedData','xcuserdata','*.xcuserstate','*.xcscmblueprint','*.podspec.json','/Carthage','/Example/build', '/Example/Pods']
    with open(os.path.join(os.getcwd(), '.gitignore'),'r+') as file:
        for line in file.readlines():
            if  '.DS_Store' in line and '.DS_Store' in strings:  
                strings.remove('.DS_Store')
                continue
            if  'build/' in line and 'build/' in strings:
                strings.remove('build/')
                continue
            if 'zip' in line and '/zip' in strings:
                strings.remove('/zip')
                continue
            if 'DerivedData' in line and 'DerivedData' in strings:
                strings.remove('DerivedData')
                continue
            if 'xcuserdata' in line and 'xcuserdata' in strings:
                strings.remove('xcuserdata')
                continue
            if 'xcuserstate' in line and '*.xcuserstate' in strings:
                strings.remove('*.xcuserstate')
                continue
            if 'xcscmblueprint' in line and '*.xcscmblueprint' in strings:
                strings.remove('*.xcscmblueprint')
                continue
            if '.podspec.json' in line and '*.podspec.json' in strings:
                strings.remove('*.podspec.json')
                continue
            if 'Carthage' in line and '/Carthage' in strings:
                strings.remove('/Carthage')
                continue
            if 'Example/build' in line and 'Example/build' in strings:
                strings.remove('/Example/build')
                continue
            if  '/Example/Pods' in line and '/Example/Pods' in strings: 
                strings.remove('/Example/Pods')
                continue
        
    with open(os.path.join(os.getcwd(), '.gitignore'),'a') as file:
        for s in strings:
            file.write(s + '\n')
            file.flush()



def upload_aliyun(dirname,path, file):

    auth = oss2.Auth(key, secret)
    bucket = oss2.Bucket(auth, url, bucketname)
    
    dir_create_result = False
    exit = bucket.object_exists(dirname)
    if exit == False:
        dir_result = bucket.put_object(dirname,"")
        if dir_result.status == 200:
            dir_create_result = True
    else:
        dir_create_result = True
    
    dir_ = file
    if dir_create_result:
        dir_ = "{0}/{1}".format(dirname,file)
    else:
        pass
    result = bucket.put_object_from_file(dir_, path)
    if result.status == 200:
        return (result.status,download_host + dir_, None)
    else:
        return (result.status,None,"")



def copy_framework(name):
    global license_path
    frameworks = glob.glob('Carthage/Build/iOS/{0}.framework'.format(name))
    for framework in frameworks:
        basename = os.path.basename(framework)
        if os.path.exists('zip/' + basename):
            os.makedirs('zip/' + basename)
        shutil.copytree(framework,'zip/' + basename)
    if not license_path is '': 
        shutil.copyfile(license_path, 'zip/' + os.path.basename(license_path))


def clear_json(json_data):
    if 'source_files' in json_data:
        json_data.pop('source_files')
    if 'exclude_files' in json_data:
        json_data.pop('exclude_files')
    
    if 'header_dir' in json_data:
        json_data.pop('header_dir')
    
    if 'header_mappings_dir' in json_data:
        json_data.pop('header_mappings_dir')
    
    if 'public_header_files' in json_data:
        json_data.pop('public_header_files')
    
    if 'private_header_files' in json_data:
        json_data.pop('private_header_files')
    
    if 'exclude_files' in json_data:
        json_data.pop('exclude_files')
    
    if 'resource_bundles' in json_data:
        json_data.pop('resource_bundles') 
    if 'license' in json_data:
        json_data.pop('license') 

def update_bin_pod_json_file(version,json_file_path,zip_path, http_source):
    with open(json_file_path,) as json_file:
        json_data = json.load(json_file)
        if 'version' in json_data:
            json_data['version'] = version
        # update source
        if ('source' in json_data):
            source_node = json_data['source']
            source_node.clear()
            source_node['http'] = http_source

        clear_json(json_data)
        
        if 'subspecs' in json_data:
            for subspec in json_data['subspecs']:
                
                clear_json(subspec)
                
                if 'dependencies' in subspec:
                    keys = subspec['dependencies'].keys()
                    for key in list(keys):
                        if '/' in key:
                            subspec['dependencies'].pop(key)
                subspec['vendored_frameworks'] = 'zip/{0}.framework'.format(name)
        else:
            json_data['vendored_frameworks'] = 'zip/{0}.framework'.format(name)

        with open(json_file_path,'w') as outfile:
            json.dump(json_data,outfile)
            return True
    return  False

def update_pod_json_file(version, path): 
    global license_path
    dirname = os.path.dirname(path)
    pod_json_files = glob.glob(dirname + '/*.podspec.json')   
    if len(pod_json_files) <= 0:
        return False 
    with open(pod_json_files[0],) as json_file:
        json_data = json.load(json_file)  
        if 'version' in json_data:
            json_data['version'] = version 
        if 'source' in json_data:
            source_data = json_data['source'] 
            if 'tag' in source_data:
                source_data['tag'] = version 
            json_data['source'] = source_data
        if 'license' in json_data: 
            json_data.pop('license') 
            # if 'file' in json_data['license']:
            #     files = glob.glob(dirname + '/' + json_data['license']['file']) 
            #     if len(files) > 0:
            #         license_path = files[0]

        with open(pod_json_files[0],'w') as outfile:
            json.dump(json_data,outfile)
            return True
    return False




def update_version(path,version,newVersion):
    line_number = subprocess.run("grep -nE 's.version.*=' {0} | cut -d : -f1".format(path),shell=True,stdout=subprocess.PIPE,encoding='UTF-8').stdout.replace("\n", "")
    shell_t =  "sed -i \"\" \"{0}s/{1}/{2}/g\" {3}".format(line_number,version,newVersion,path)
    result = subprocess.run(shell_t,shell=True,stdout=subprocess.PIPE,encoding='UTF-8').stderr
    if not result:
        return  True
    return  False

def fail_work(is_exit): 
    reset_workspace()
    os.system('git stash pop')
    os.system('git stash drop')
    if is_exit is True:
        exit()

# '/Users/niezi/Documents/framework/TKFrameworkLib/jenkinsRunner/Example/Podfile'
# update_version('/Users/niezi/Documents/framework/TKFrameworkLib/jenkinsRunner/jenkinsRunner.podspec','0.1.2','0.1.3')
#
pod_list = check_has_podspec_file()
if len(pod_list) <= 0:
    print('this is not pod project workspace, please run from pod project workspace')
    exit()

pod_file = check_profile()
if not pod_file:
    print('not found Podfile，please check')
    exit()

# 重置工作区域 主要是文件
reset_workspace()

s = subprocess.run('git status -s',shell=True,stdout=subprocess.PIPE,encoding='UTF-8').stdout.replace("\n", "")
if not s is '':
    # 暂存更改或者新建的文件
    print('stash changed or created files')
    os.system('git stash')


newVersion = ''
message = ''
branch = 'master'
is_checkout_branch = 'y'
license_path = ''


current_branch = subprocess.run('git symbolic-ref --short -q HEAD',shell=True,stdout=subprocess.PIPE,encoding='UTF-8').stdout.replace("\n", "")

b = input('请输入分支名(default {0}):'.format(current_branch))
if not b is '':
    branch = b

if branch != current_branch:
    checkout = input('是否要切换到 >>> {0} <<<< 分支？\n 输入 y or n 默认为 y: '.format(b))
    if not (checkout is '' or 'y'):
        fail_work(True)
    s = subprocess.run('git checkout {0}'.format(b) ,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE, encoding='UTF-8')
    if s.returncode < 0:
        print(s.stderr)
        fail_work(True)



os.system('git pull origin {0} --tags'.format(branch))


transition_spec_to_json(pod_list[0])
name, version = get_version_and_name(pod_list[0] + '.json')

while not newVersion:
    newVersion = input('currentVersion: {0}\n请输入版本号:'.format(version))


while not message:
    message = input('请输入commit log:')


print("===============================================================")
print('\n\n')
print('             Current Version:{0}                     '.format(version))
print('                 New Version:{0}                     '.format(newVersion))
print('                     Message:{0}                     '.format(message))
print('                     分支:   :{0}                     '.format(branch))
print('\n\n')
print("===============================================================")
print('\n')

print("🏃🏃🏃🏃🏃🏃🏃🏃🏃🏃🏃🏃🏃🏃🏃🏃Building🏃🏃🏃🏃🏃🏃🏃🏃🏃🏃🏃🏃🏃🏃🏃🏃🏃🏃")
#git操作

update_version(pod_list[0],version,newVersion) 
# update_gitignore()
check_Carthage()
update_profile(pod_file)
pod_install(os.path.abspath(os.path.dirname(pod_file)))


os.system('git add .')
os.system('git tag -d {0}'.format(newVersion))
os.system('git commit -m "{0} and update {1}"'.format(message, newVersion))
os.system('git tag {0}'.format(newVersion))
os.system('git push origin {0} --tags'.format(branch))

if not update_pod_json_file(newVersion,pod_list[0]):
    print('upload json file failed, please check')
    fail_work(True)  

push_shell = 'pod repo update {0} && pod repo push {1} {2} --verbose --allow-warnings  --sources={3}'.format('TKSpec','TKSpec',pod_list[0] + '.json',source_pod_spec)
result_pp = subprocess.run(push_shell,shell=True,encoding='UTF-8')
if result_pp.returncode < 0:
    print(result_pp.stderr)
    fail_work(True)


if  carthage_build() == False:
    print('build faild')
    fail_work(True)
copy_framework(name)

if not os.listdir('./zip/'):
    print('build failed')
    fail_work(True)

os.system('zip -q -r ./zip/{0}-{1}.zip ./zip/'.format(name,newVersion))

status,url,error = upload_aliyun(name,'./zip/{0}-{1}.zip'.format(name,newVersion), '{0}-{1}.zip'.format(name,newVersion))
if status != 200:
    print('upload failed: {0}'.format(error))
    fail_work(True)


if not update_bin_pod_json_file(newVersion,pod_list[0] + '.json','./zip/{0}-{1}.zip'.format(name,newVersion),url):
    print('upload json file failed, please check')
    fail_work(True)  


print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>Building end >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")


print("🏃🏃🏃🏃🏃🏃🏃🏃🏃🏃🏃🏃🏃🏃🏃🏃 upload 🏃🏃🏃🏃🏃🏃🏃🏃🏃🏃🏃🏃🏃🏃🏃🏃🏃🏃")

# --skip-import-validation
push_shell = 'pod repo update {0} && pod repo push {1} {2} --verbose --allow-warnings  --sources={3}'.format('BinSpec','BinSpec',pod_list[0] + '.json',binary_pod_spec)
result_pp = subprocess.run(push_shell,shell=True,encoding='UTF-8')
if result_pp.returncode < 0:
    print(result_pp.stderr)
    fail_work(True)
# 更新 podspec文件
fail_work(False)

