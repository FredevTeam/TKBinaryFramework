import os
import json
import glob
import datetime
import shutil
import oss2
import subprocess
from enum import Enum

import fnmatch


config = {} 
global_log_path = ''
debug = False


class WorkSpaceType(Enum):
    Non = 0
    WorkSpace = 1
    Project = 2


# 重置工作区
def reset_workspace(path):
    subprocess.run('git clean -df', shell=True)
    subprocess.run('git reset --hard', shell=True)
    # if os.path.isdir(os.path.join(path, 'Carthage')):
    #     shutil.rmtree(os.path.join(path, 'Carthage'))
    if os.path.exists(os.path.join(path,'build')):
        shutil.rmtree(os.path.join(path,'build'))

# 是否需要更新
def git_check():
    head_count = subprocess.run('git rev-list HEAD --count', shell=True).stdout
    master_count = subprocess.run('git rev-list origin/master --count', shell=True).stdout
    if head_count == master_count:
        return False
    return True

# log 
def begin_log_point(stream,title):
    if debug:
        print("{0}: >>>>>>>>>>>>>>>>>>>>>>>>\n".format(title))
    else:
        stream.write('\n\n\n')
        stream.write("{0}: >>>>>>>>>>>>>>>>>>>>>>>>\n".format(title))
        stream.flush()

# end log 
def end_log_point(stream, title):
    if debug:
        print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<:{0}\n\n".format(title))
    else:
        stream.write("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<:{0}\n\n".format(title))
        stream.write('\n\n\n')
        stream.flush()

# 监测是否有 cartfile 
def check_Carthage(path):
    if not os.path.isfile(path + '/Cartfile'):
        # os.system('touch {0}/Cartfile'.format(path))
        return  False
    return True

#=============Xcode ===========================
def xcode_clean(log_file, workspace, project,scheme_name, mode, swift_version):
    """
    :param log_file: 日志
    :param workspace:
    :param project:
    :param scheme_name:
    :param mode: 模式 Debug / release
    :return:
    """
    input = None if debug == True else log_file

    begin_log_point(input, '>>>>>>>>>>>>>>>>>>>Begin clean .>>>>>>>>>>>>>>>>>>>>>')

    command_iphone = ''
    command_simulator = ''
    if workspace is not None:
        if 'xcworkspace' not in workspace:
            begin_log_point(input, 'this is not a correct workspace {0}'.format(workspace))
            return False
        command_iphone = 'xcodebuild ' \
                         '-workspace {0} ' \
                         '-scheme "{1}" ' \
                         '-sdk iphoneos ' \
                         '-configuration {2} ' \
                         'SWIFT_VERSION={3} ' \
                         'clean'.format(workspace,scheme_name,mode,swift_version)
        command_simulator = 'xcodebuild ' \
                            '-workspace {0} ' \
                            '-scheme "{1}" ' \
                            '-sdk iphonesimulator ' \
                            '-configuration {2} ' \
                            'SWIFT_VERSION={3} ' \
                            'clean'.format(workspace,scheme_name,mode,swift_version)
        pass
    elif project is not None:
        if 'xcodeproj' not in project:
            begin_log_point(input, 'this is not a correct project {0}'.format(project))
            return False
        command_iphone = 'xcodebuild ' \
                         '-workspace {0} ' \
                         '-scheme "{1}" ' \
                         '-sdk iphoneos ' \
                         '-configuration {3} ' \
                         'SWIFT_VERSION={4} ' \
                         'clean'.format(project, scheme_name, mode,swift_version)
        command_simulator = 'xcodebuild ' \
                            '-workspace {0} ' \
                            '-scheme "{1}" ' \
                            '-sdk iphonesimulator ' \
                            '-configuration {3} ' \
                            'SWIFT_VERSION={4} ' \
                            'clean'.format(project, scheme_name, mode,swift_version)
        pass
    else:
        pass

    if command_simulator is '' and command_iphone is '':
        begin_log_point('command is nil please check')
        return False

    iphoneos_p = subprocess.run(command_iphone, stdout=input,stderr=input, shell=True)
    simulator_p = subprocess.run(command_simulator, stdout=input, stderr=input,shell=True)
    end_log_point(input, '<<<<<<<<<<<<<<<<<<<<<<<<<<<<<End Clean <<<<<<<<<<<<<<<<<<<<<<<<<<<')
    if iphoneos_p.returncode == 0 and simulator_p.returncode == 0:
        return True
    return False

def xcode_build(log_file, workspace, project , scheme_name, swift_version, mode,sdk ,mach_o_type):
    """

    :param login_file: 日志
    :param workspace:
    :param project:
    :param scheme_name:
    :param swift_version:
    :param mode:  模式 Debug / Release
    :param sdk: 真机， 模拟器
    :param mach_o_type:  静态 动态
    :return:
    """
    input = None if debug == True else log_file

    begin_log_point(input, '>>>>>>>>>>>>>>>>>>>Begin clean .>>>>>>>>>>>>>>>>>>>>>')

    # 没进入来啊
    base_p =  os.path.abspath(os.path.join(workspace, '..'))

    build_path = os.path.join(base_p, 'build');
    archive = 'archive -archivePath {0}'.format(build_path) if sdk == 'iphoneos' else ''
    command_iphoneos = ''
    command_sim = ''
    if workspace is not None:
        if mode == 'debug':
            command_sim = 'xcodebuild ' \
                          '-workspace {0} ' \
                          '-scheme "{1}" ' \
                          '-configuration {2} ' \
                          '-sdk {3} ' \
                          '-derivedDataPath {4} ' \
                          'ONLY_ACTIVE_ARCH=NO ' \
                          'CODE_SIGNING_REQUIRED=NO ' \
                          'CODE_SIGN_IDENTITY= ' \
                          'COPY_PHASE_STRIP=NO ' \
                          'GENERATE_PKGINFO_FILE=YES ' \
                          'COPY_PHASE_STRIP=NO ' \
                          'MACH_O_TYPE={5} ' \
                          'BUILD_ROOT={4} ' \
                          'BUILD_DIR={4} ' \
                          'SWIFT_VERSION={6} ' \
                          'CONFIGURATION_BUILD_DIR={4} ' \
                          'SKIP_INSTALL=YES ' \
                          'STRIP_INSTALLED_PRODUCT=NO ' \
                          'GCC_GENERATE_DEBUGGING_SYMBOLS=YES ' \
                          'DEPLOYMENT_LOCATION=YES ' \
                          'BUILT_PRODUCTS_DIR={4} ' \
                          '{7} ' \
                          'GCC_INSTRUMENT_PROGRAM_FLOW_ARCS=NO ' \
                          'CLANG_ENABLE_CODE_COVERAGE=NO ' \
                          'build'.format(workspace, scheme_name, mode, 'iphonesimulator',build_path, mach_o_type,
                                          swift_version, '')
            pass

        command_iphoneos = 'xcodebuild ' \
                           '-workspace {0} ' \
                           '-scheme "{1}" ' \
                           '-configuration {2} ' \
                           '-sdk {3} ' \
                           '-derivedDataPath {4} ' \
                           'ONLY_ACTIVE_ARCH=NO ' \
                           'CODE_SIGNING_REQUIRED=NO ' \
                           'CODE_SIGN_IDENTITY= ' \
                           'COPY_PHASE_STRIP=NO ' \
                           'GENERATE_PKGINFO_FILE=YES ' \
                           'COPY_PHASE_STRIP=NO ' \
                           'MACH_O_TYPE={5} ' \
                           'BUILD_ROOT={4} ' \
                           'BUILD_DIR={4} ' \
                           'SWIFT_VERSION={6} ' \
                           'CONFIGURATION_BUILD_DIR={4} ' \
                           'SKIP_INSTALL=YES ' \
                           'STRIP_INSTALLED_PRODUCT=NO ' \
                           'DEPLOYMENT_LOCATION=YES ' \
                           'BUILT_PRODUCTS_DIR={4} ' \
                           '{7} ' \
                           'GCC_INSTRUMENT_PROGRAM_FLOW_ARCS=NO ' \
                           'CLANG_ENABLE_CODE_COVERAGE=NO ' \
                           'build'.format(workspace, scheme_name, mode, 'iphoneos',build_path, mach_o_type,
                                          swift_version, archive)

        pass
    elif project is not None:
        if mode == 'debug':
            command_sim = 'xcodebuild ' \
                      '-project {0} ' \
                      '-scheme "{1}" ' \
                      '-configuration {2} ' \
                      '-sdk {3} ' \
                      '-derivedDataPath {4} ' \
                      'ONLY_ACTIVE_ARCH=NO ' \
                      'CODE_SIGNING_REQUIRED=NO ' \
                          'CODE_SIGN_IDENTITY= ' \
                          'COPY_PHASE_STRIP=NO ' \
                          'GENERATE_PKGINFO_FILE=YES ' \
                          'COPY_PHASE_STRIP=NO ' \
                      'MACH_O_TYPE={5} ' \
                      'BUILD_ROOT={4} ' \
                      'BUILD_DIR={4} ' \
                      'SWIFT_VERSION={6} ' \
                      'CONFIGURATION_BUILD_DIR={4} ' \
                      'SKIP_INSTALL=YES ' \
                          'STRIP_INSTALLED_PRODUCT=NO ' \
                          'DEPLOYMENT_LOCATION=YES ' \
                      'BUILT_PRODUCTS_DIR={4} ' \
                      '{7} ' \
                      'GCC_INSTRUMENT_PROGRAM_FLOW_ARCS=NO CLANG_ENABLE_CODE_COVERAGE=NO ' \
                      'build'.format(project, scheme_name, mode, 'iphonesimulator',build_path, mach_o_type,
                                      swift_version, '')
            pass
        command_iphoneos = 'xcodebuild ' \
                  '-project {0} ' \
                  '-scheme "{1}" ' \
                  '-configuration {2} ' \
                  '-sdk {3} ' \
                  '-derivedDataPath {4} ' \
                  'ONLY_ACTIVE_ARCH=NO ' \
                  'CODE_SIGNING_REQUIRED=NO ' \
                           'CODE_SIGN_IDENTITY= ' \
                           'COPY_PHASE_STRIP=NO ' \
                           'GENERATE_PKGINFO_FILE=YES ' \
                           'COPY_PHASE_STRIP=NO ' \
                  'MACH_O_TYPE={5} ' \
                  'BUILD_ROOT={4} BUILD_DIR={4} ' \
                  'SWIFT_VERSION={6} ' \
                  'CONFIGURATION_BUILD_DIR={4} ' \
                  'SKIP_INSTALL=YES ' \
                           'STRIP_INSTALLED_PRODUCT=NO ' \
                           'DEPLOYMENT_LOCATION=YES ' \
                  'BUILT_PRODUCTS_DIR={4} ' \
                  '{7} ' \
                  'GCC_INSTRUMENT_PROGRAM_FLOW_ARCS=NO CLANG_ENABLE_CODE_COVERAGE=NO ' \
                  'build'.format(project, scheme_name, mode, 'iphoneos',build_path, mach_o_type,
                                  swift_version, archive)

        pass
    else:
        pass


    if mode == 'debug':
        if command_iphoneos is '' or command_sim is '':
            begin_log_point('command is nil please check')
            return False
            pass
        p = subprocess.run(command_iphoneos, stdout=input, stderr=input, shell=True)
        sim_p = subprocess.run(command_sim, stdout=input, stderr=input, shell=True)
        print("构建完成")
        if p.returncode == 0 and sim_p.returncode == 0:
            return  True
    else:
        if command_iphoneos is '':
            begin_log_point('command is nil please check')
            return False
            pass
        p = subprocess.run(command_iphoneos, stdout=input,stderr=input, shell=True)
        if p.returncode == 0:
            return True
    return False

def xcode_cop_framework(base_path):
    path = os.path.abspath(os.path.dirname(base_path))
    iphoneos_path = os.path.join(path,'build/Build/Intermediates.noindex/UninstalledProducts/iphoneos')
    iphonesimulator_path = os.path.join(path,'build/Build/Intermediates.noindex/UninstalledProducts/iphonesimulator')
    mode = config['mode'] if 'mode' in config else 'release'
    if mode == 'release':
        frameworks = glob.glob('{0}/*.framework'.format(iphoneos_path))
        if len(frameworks) <= 0:
            return False
        for framework in frameworks:
            basename = os.path.basename(framework)
            if os.path.exists('zip/' + basename):
                os.makedirs('zip/' + basename)
            shutil.copytree(framework,'zip/' + basename)
            return True
        pass
    else:
        iphoneos_frameworks = glob.glob('{0}/*.framework'.format(iphoneos_path))
        iphonesimulator_frameworks = glob.glob('{0}/*.framework'.format(iphonesimulator_path))
        if len(iphoneos_frameworks) == 0 or len(iphonesimulator_frameworks) == 0:
            return False
        lipo_framework_path = lipo_framework(iphoneos_frameworks[0], iphonesimulator_frameworks[0])
        if lipo_framework_path == None:
            return  False
        basename = os.path.basename(lipo_framework_path)
        if os.path.exists('zip/' + basename):
            os.makedirs('zip/' + basename)
        shutil.copytree(lipo_framework_path, 'zip/' + basename)
        return True

    return  False

def lipo_framework(iphoneos_path, iphonesumulator_path):
    if os.path.basename(iphoneos_path) != os.path.basename(iphonesumulator_path):
        return  None
    path = os.path.abspath(os.path.join(iphoneos_path, "../.."))
    base_name = os.path.basename(iphoneos_path)
    unified_path = os.path.join(path,'Unified')

    names = base_name.split('.')
    if len(names) <=0:
        return None

    bin_name = ''
    for fpath, dirname, fnames in os.walk(iphoneos_path):
        if bin_name != '':
            break
        for name in fnames:
            if names[0] in name and bin_name == '':
                bin_name = name
                break


    if os.path.exists(unified_path):
        shutil.rmtree(unified_path)

    os.makedirs(unified_path)
    shutil.copytree(iphoneos_path, os.path.join(unified_path, base_name))
    # os.system("cp -frp '{0}' '{1}'".format(iphonesumulator_path,os.path.join(unified_path, base_name)))
    os.system("cp -frp '{0}' '{1}'".format(iphonesumulator_path + '/', os.path.join(unified_path, base_name + '/')))

    # lipo - create
    # 真机路径
    # 模拟器路径 - output
    # 真机路径
    command = "lipo -create '{0}' '{1}' -output '{2}'".format(os.path.join(iphoneos_path,bin_name), os.path.join(iphonesumulator_path, bin_name), os.path.join(unified_path,base_name,bin_name))
    result = subprocess.run(command, shell=True)
    if result.returncode == 0 :
        return os.path.join(unified_path, base_name)
    return None



def get_workspace_or_project(path, workspace_name):
    """
    :param path:
    :return: (WorkSpaceType , name, path, scheme_name)
    """
    xworkspace = []
    xcodeproj = []
    for fpath, dirname, fnames in os.walk(path):
        for name in dirname:
            if '.xcworkspace' in name:
                xworkspace.append(os.path.join(fpath, name))
            if '.xcodeproj' in name:
                xcodeproj.append(os.path.join(fpath, name))

    if len(xworkspace) > 0:
        result = subprocess.run('xcodebuild -workspace {0} -list -json'.format(xworkspace[0]), shell=True, encoding='UTF-8', stdout=subprocess.PIPE).stdout
        json_dic = json.loads(s=result)
        name = os.path.basename(xworkspace[0])
        if 'name' in json_dic:
            name = json_dic['name']
        scheme = workspace_name
        mapping_scheme = ''
        if 'mapping' in config and workspace_name in config['mapping']:
            mapping_scheme = config['mapping'][workspace_name]
            if 'schemes' in json_dic['workspace']:
                schemes = json_dic['workspace']['schemes']
                if mapping_scheme in schemes:
                    scheme = mapping_scheme
        return (WorkSpaceType.WorkSpace, name,xworkspace[0], scheme)
    if len(xcodeproj) > 0:
        result = subprocess.run('xcodebuild -project {0} -list -json'.format(xcodeproj[0]), shell=True, encoding='UTF-8', stdout=subprocess.PIPE).stdout
        json_dic = json.loads(s = result)
        name = os.path.basename(xcodeproj[0])
        if 'name' in json_dic:
            name = json_dic['name']
        scheme = workspace_name
        mapping_scheme = ''
        if 'mapping' in config and workspace_name in config['mapping']:
            mapping_scheme = config['mapping'][workspace_name]
            if 'schemes' in json_dic['project'] and mapping_scheme in json_dic['project']['schemes']:
                scheme = mapping_scheme
        return (WorkSpaceType.Project, name, xcodeproj[0], scheme)

    return (WorkSpaceType.Non, None, None, None)

# =============================================



# 监测是否有 profile 文件
def check_profile(path):
    podfiles = []
    for fpath, dirname, fnames in os.walk(path):
        for name in fnames:
            if name == 'Podfile':
                podfiles.append(os.path.join(fpath,name))
    if len(podfiles) > 0:
        return  podfiles[0]

    # if os.path.exists(path + '/Podfile'):
    #     return os.path.join(path, 'Podfile')
    # if os.path.exists(path + '/Example'):
    #     if os.path.exists(path + '/Example/Podfile'):
    #         return os.path.join(path, 'Example/Podfile')
    #
    return  None

# 更新 profile  
def update_profile(path):
    shell_text = "grep -c \"{0}\" {1}".format('share_schemes_for_development_pods',path)
    exists = subprocess.run(shell_text,shell=True,stdout=None,encoding='UTF-8').stdout
        # .replace("\n", "")
    if not exists is None:
        if int(exists) > 0:
            return
    
    if os.path.exists(path):
        with open(path,'a') as file:
            text = "install! 'cocoapods',:share_schemes_for_development_pods => true"
            file.write('\n')
            file.write(text)


# pod install 
def pod_install(log_file, path):
    p = os.path.dirname(path)
    enter = False
    if p == os.getcwd():
        pass
    else:
        os.chdir(p)
        enter = True
    input = None if debug ==True else log_file
    # "变量1" if a > b else "变量2"
    subprocess.run('pod install', shell=True, stdout= input,stderr= input, encoding="utf-8")
    if enter == True:
        os.chdir(os.path.abspath(os.path.dirname(os.getcwd())))

def carthage_build(log_file):
    input = None if debug == True else log_file
    p = subprocess.run('carthage update --platform ios --no-use-binaries  --verbose', stdout=input,stderr=input, shell=True)
    # p = subprocess.run('ls', shell=True)
    pp = subprocess.run('carthage build --no-skip-current --platform ios  --verbose', stdout=input,stderr=input,
                        shell=True)
    # pp = subprocess.run('ls', shell=True)
    if p.returncode == 0 and pp.returncode == 0:
        return  True
    return  False

def reset_zip_dir():
    if not os.path.exists('zip/'):
        os.mkdir('zip')
    else:
        shutil.rmtree('zip')
        os.mkdir('zip')

def copy_framework():
    frameworks = glob.glob('Carthage/Build/iOS/*.framework')
    if len(frameworks) <= 0:
        return False

    for framework in frameworks:
        basename = os.path.basename(framework)
        if os.path.exists('zip/' + basename):
            os.makedirs('zip/' + basename)
        shutil.copytree(framework,'zip/' + basename)
    return True

def transition_spec_to_json(log_file, files):
    input = None if debug == True else log_file
    podspec_Jsons = {}
    for podspec in files:
        basename = os.path.basename(podspec)
        pod_json_files = glob.glob(podspec + '.json')
        if len(pod_json_files) == 0:
            subprocess.run('pod ipc spec ' + podspec + ' >> ' + podspec + '.json',shell=True,stdout=input,stderr=input,encoding="utf-8")
            podspec_Jsons[basename.split('.')[0]] = podspec+'.json'
        else:
            podspec_Jsons[basename.split('.')[0]] = podspec + '.json'
    if len(podspec_Jsons.keys()) == len(files):
        return podspec_Jsons
    return None

def get_all_podspec():
    podspec_list = []
    podspec_list.extend(glob.glob(os.getcwd() + '/*.podspec'))
    path = 'Carthage/Checkouts'
    if os.path.exists(path):
        dir_list = os.listdir(path)
        for dir in dir_list:
            podspec_list.extend(glob.glob(os.path.join(os.getcwd(),path,dir, '*.podspec')))

    return  podspec_list

def get_version(path):
    with open(path) as json_file:
        json_data = json.load(json_file)
        if ("version" in json_data):
            return json_data['version']
    return None


def ziping(pod_json_dic):
    messages = []
    for key in pod_json_dic.keys():
        version = get_version(pod_json_dic[key])
        if not version:
            return None
        os.system('zip -q -r ./zip/{0}-{1}.zip ./zip/{2}.framework'.format(key,version,key))
        messages.append((key, version,pod_json_dic[key]))
    return messages

def upload_aliyun(pod_name,file_name, path):
    if "upload" in config:
        upload = config["upload"]
        if ("key" in upload) and ("secret" in upload) and ("url" in upload) and ('bucketname' in upload) and (
                'download_host' in upload):

            auth = oss2.Auth(upload["key"], upload["secret"])
            # 开启日志
            # date = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            # oss2.set_file_logger('{0}-{1}.log'.format(date,file_name), 'oss2', logging.INFO)
            bucket = oss2.Bucket(auth, upload["url"], upload["bucketname"])
            mode = config['mode'] if 'mode' in config else 'other'
            result = bucket.put_object_from_file('{0}/{1}/{2}'.format(pod_name,mode, file_name), path)

            if result.status == 200: 
                return (result.status,file_name, '{0}/{1}/{2}/{3}'.format(upload["download_host"], pod_name,mode,file_name), None)
            else:
                return (result.status,file_name, None, "")
        return (-1, None, "upload prarm is faild , please check")
    return (-1,file_name, None, "config file not found upload key")


def aliyun_check_file_exist(pod_name,file_name):
    if "upload" in config:
        upload = config["upload"]
        if ("key" in upload) and ("secret" in upload) and ("url" in upload) and ('bucketname' in upload):
            auth = oss2.Auth(upload["key"], upload["secret"])
            bucket = oss2.Bucket(auth, upload["url"], upload["bucketname"])
            exist = bucket.object_exists('{0}/{1}'.format(pod_name,file_name))
            if exist:
                return True
    return  False


def update_pod_json_file(args, result):
    name, version, path = args
    http_source = ''
    if result:
        http_source = result[2]
    else:
        if  "upload" in config  and ('download_host' in config['upload']):
            http_source = config['upload']['download_host'] + '{0}-{1}.zip'.format(name,version)
        else:
            return  False
    with open(path) as json_file:
        json_data = json.load(json_file)
        # update source
        if ('source' in json_data):
            source_node = json_data['source']
            source_node.clear()
            source_node['http'] = http_source

        if 'source_files' in json_data:
            json_data.pop('source_files')
        if 'exclude_files' in json_data:
            json_data.pop('exclude_files')
        if 'subspecs' in json_data:
            for subspec in json_data['subspecs']:
                if 'source_files' in subspec:
                    subspec.pop('source_files')
                if 'dependencies' in subspec:
                    keys = subspec['dependencies'].keys()
                    for key in list(keys):
                        if '/' in key:
                            subspec['dependencies'].pop(key)
                subspec['vendored_frameworks'] = 'zip/{0}.framework'.format(name)
        else:
            json_data['vendored_frameworks'] = 'zip/{0}.framework'.format(name)
        with open(path,'w') as outfile:
            json.dump(json_data,outfile,indent=4)
            return True
    return  False

def push_pod_json_file(log,path):
    input = None if debug == True else log
    mode = config['mode'] if 'mode' in config else ''
    if mode == '':
        print("please set mode on config file")
        return False
    if os.path.exists(path):
        if 'pod' in config and mode in config['pod']:
            if ('source' in config['pod'][mode]) and ('spec_name' in config['pod'][mode]):
                pod_upload = 'pod repo push {0} {1} --verbose --allow-warnings --skip-import-validation  --sources={2}'.format(config['pod'][mode]['spec_name'],path,','.join(config['pod'][mode]['source']))
                pu = subprocess.run(pod_upload, stdout=input, stderr=input, shell=True)
                if pu.returncode == 0:
                    return  True
                else:
                    log.write('pod repo push Fail')

    return  False


def worker(args):
    """
    worker function
    return tips
        status: True/False
        message: Supplementary information，this function run to generate data
        desc: desc message
        path: work path os.getcwd()
        projectName: workspace_name dir name or project name

    """
    global config 
    global global_log_path
    global debug

    workspace_path, config, global_log_path = args
    debug = True if config['mode'] == 'debug' else False



    workspace_name = os.path.basename(workspace_path)
    # 进入工作目录 
    os.chdir(workspace_path)
    print("=========workspace_path:=={0},=========os:{1}".format(workspace_path, os.getcwd()))
    reset_workspace(workspace_path)




    if git_check() == False and config['git']['force'] == False:
        return (True, None, None, workspace_path, workspace_name)


    date = datetime.datetime.now().strftime("%Y-%m-%d-%H")
    file_path = os.path.join(global_log_path,'{0}-{1}.log'.format(workspace_name, '' if debug else date))


    with open(file_path,'a+') as fdout:
        begin_log_point(fdout,'==================>>>>>>>>>>>>>>>>>>>>>>>> \n\n\n')
        begin_log_point(fdout,"=========workspace_path:=={0},=========os:{1}".format(workspace_path, os.getcwd()))
        #==================================================#
        begin_log_point(fdout,'pod')
        pod_file = check_profile(workspace_path)
        if pod_file:
            update_profile(pod_file)
            pod_install(fdout,pod_file)
        end_log_point(fdout,'pod')

        begin_log_point(fdout,"carthage build")
        carthage_file = check_Carthage(workspace_path)
        if carthage_file:
            if not carthage_build(fdout):
                return (False, None, 'carthage build filed', workspace_path, workspace_name)
        end_log_point(fdout,"carthage build")
        #==================================================#


        #==================================================#
        #(WorkSpaceType, name, path, scheme_name)
        xtype, name,path, scheme_name = get_workspace_or_project(workspace_path, workspace_name)
        mode = config['mode'] if 'mode' in config else 'debug'
        swift_version = config['swift_version'] if 'swift_version' in config else '4.2'
        mach_o_type = config['mach_o_type'] if 'mach_o_type' in config else 'staticlib'
        sdk = config['sdk'] if 'sdk' in config else 'all'
        if xtype == WorkSpaceType.Non:
            return (False, None, 'this {0} is not found .xworkspace and .xcodeproj  project , please check'.format(workspace_name), workspace_path, workspace_name)
            pass
        if xtype == WorkSpaceType.WorkSpace:
            #  project,scheme_name, mode, swift_version
            xcode_clean(fdout,path,None,scheme_name ,mode,swift_version)
            xcode_build(fdout, path,None,scheme_name,swift_version, mode,sdk,mach_o_type)
            pass
        if xtype == WorkSpaceType.Project:
            xcode_clean(fdout, None, path,scheme_name,mode, swift_version)
            xcode_build(fdout,None,path,scheme_name,swift_version,mode,sdk,mach_o_type)
            pass



        begin_log_point(fdout, 'xcode build')
        #==================================================#


        #==================================================#
        begin_log_point(fdout,'zip framework')
        reset_zip_dir()

        #======Xcodebuild code framework ========#
        if xcode_cop_framework(path) is False:
            return (False,None,'build faild or not has framework',workspace_path, workspace_name)

        # if copy_framework() is False:
        #     return (False,None,'build faild or not has framework',workspace_path, workspace_name)


        podfile_jsons =  transition_spec_to_json(fdout,get_all_podspec())
        if not podfile_jsons:
            fdout.write('transition spec to json spec faile {0}'.format(get_all_podspec()))
            fdout.flush()
            return (False,podfile_jsons,'transition spec to json faild',workspace_path, workspace_name)

        podfile_messages = ziping(podfile_jsons)
        if not podfile_messages:
            fdout.write('zip is faild , please check')
            fdout.flush()
            return  (False,podfile_messages,'zip faild',workspace_path, workspace_name)

        end_log_point(fdout,'zip framework')
        # #==================================================#


        begin_log_point(fdout,'upload')
        podfile_messages_copy = podfile_messages[:]
        upload_results = []

        for ms in podfile_messages_copy[:]:
            pod_name, pod_version,_ = ms
            # if not aliyun_check_file_exist(pod_name,'{0}.zip'.format(pod_version)):
            upload_results.append(upload_aliyun(pod_name,'{0}.zip'.format(pod_version),'./zip/{0}-{1}.zip'.format(pod_name,pod_version)))
            # else:
                # podfile_messages_copy.remove(ms)
                # print((200,'{0}.zip'.format(pod_version),'{0}/{1}/{2}'.format(upload["download_host"], pod_name, '{0}.zip'.format(pod_version)),None))
                # upload_results.append((200,'{0}.zip'.format(pod_version),'{0}/{1}/{2}'.format(upload["download_host"], pod_name, '{0}.zip'.format(pod_version)),None))
        print(upload_results)
        if len(upload_results) != len(podfile_messages_copy):
            for r in upload_results:
                code,name,_,error = r
                if code != 200 :
                    fdout.write("upload failed name:{0}, code:{1}, error:{2} \n".format(name,code,error))
                    fdout.flush()

            print("upload faild {0}", upload_results)
            return (False,upload_results,'upload failed',workspace_path,workspace_name)

        end_log_point(fdout, 'upload')


        begin_log_point(fdout,'upload podfile.json')
        # change podspec.json file
        for index in range(len(podfile_messages)):
            podfile_m = podfile_messages[index]
            result = None
            if index < len(upload_results):
                result = upload_results[index]
            update_pod_json_file(podfile_m,result)

        end_log_point(fdout, 'upload podfile.json')

        #vild
        begin_log_point(fdout,'pod push')
        error_p = []
        for index in range(len(podfile_messages)):
            n,v,p = list(reversed(podfile_messages))[index]
            if not push_pod_json_file(fdout,p):
                error_p.append(n + v + p)

        if len(error_p):
            return (False,error_p,'pod push faild',workspace_path, workspace_name)
        end_log_point(fdout,'pod push')
        end_log_point(fdout,'{0} ==================>>>>>>>>>>>>>>>>>>>>>>>> \n\n\n'.format(workspace_path))

    return (True,None,None,workspace_path,workspace_name)

