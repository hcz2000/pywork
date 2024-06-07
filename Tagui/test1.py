from flexx import flx

class FlexxTest(flx.Widget):
    #内置CSS定义样式，还是要学一点html的相关知识的
    CSS = """
    .flx-Label {
        background: #9d9;
        width:200px;
        height:3px
    }
    """
    def init(self):
        flx.Label(text='hello world你好世界')

#网页的标题名和样式定义，注意这个样式是指html或body的背景颜色定义
app = flx.App(FlexxTest, title='FlexxTest', style ='background:pink;')
#导出或者保存为一张单html文件
#app.export('example.html', link=0)  # Export to single file
app.launch('browser')  # show it now in a browser
#flx.run()  # enter the mainloop
flx.start()  #与run小区别就是退出循环，还可再启动