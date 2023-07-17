import tagui as t
t.init()
t.url('http://music.163.com/#/artist/album?id=101988&limit=120&offset=0')
t.frame('g_iframe')
t.click('Legends - The Beatles (The Early Days)')
t.snap('page', 'results.png')
t.close()