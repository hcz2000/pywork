import os

class FileUtil():

    def __init__(self):
        self.basePath = os.path.dirname(__file__)

    def makedir(self, name):
        path = os.path.join(self.basePath, name)
        isExist = os.path.exists(path)
        if not isExist:
            os.makedirs(path)
            print('The file is created now.')
        else:
            print('The file existed.')
        #切换到该目录下
        os.chdir(path)
        return path

    def getFileNames(self, dir):
        file_names = os.listdir(dir)
        return file_names


if __name__ == '__main__':
    obj = FileUtil()
    obj.getFileNames('./')