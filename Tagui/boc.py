import tagui as t
import time
t.init()
t.url('https://ebsnew.boc.cn/boc15/login.html?seg=66')
t.type('txt_username_79443','hcz2000')
t.type('input_div_password_79445','sankhya2000')
#t.click('登录')
t.click('btn_login_79676')
time.sleep(2)
t.click('中银理财')
#cnt=t.count("//div[@id='NewHoldProductQuery_34']//table[@class='tb']")
#cnt=t.count("//div[@id='wrapper']/div/div/div[@id='NewHoldProductQuery_34']/div[@id='loadPagestep1']")
cnt=t.count("//div[@id='NewHoldProductQuery_34']//div")
print(cnt)
time.sleep(300)
t.snap('page', 'results.png')
t.close()