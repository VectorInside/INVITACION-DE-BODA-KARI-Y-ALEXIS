import base64
import http.client
import importlib.util
import io
import json
import tempfile
import threading
import unittest
from pathlib import Path
from PIL import Image

spec=importlib.util.spec_from_file_location('wedding',Path(__file__).with_name('server.py'))
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class WeddingTests(unittest.TestCase):
 def test_private_moderation_and_saved_rsvp(self):
  with tempfile.TemporaryDirectory() as temp:
   server=module.WeddingServer(('127.0.0.1',0),temp)
   thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
   port=server.server_address[1];origin='http://127.0.0.1:'+str(port)
   def call(method,path,data=None,cookie=None,csrf=None,foreign=False):
    headers={};payload=None
    if data is not None:headers={'Content-Type':'application/json','Origin':'https://foreign.example' if foreign else origin};payload=json.dumps(data)
    if cookie:headers['Cookie']=cookie
    if csrf:headers['X-CSRF-Token']=csrf
    conn=http.client.HTTPConnection('127.0.0.1',port);conn.request(method,path,payload,headers);response=conn.getresponse();status=response.status;cookie=response.getheader('Set-Cookie');body=response.read();conn.close()
    try:body=json.loads(body)
    except (ValueError,UnicodeDecodeError):pass
    return status,body,cookie
   try:
    self.assertEqual(call('GET','/api/admin/dashboard')[0],401)
    self.assertEqual(call('GET','/.private/auth.json')[0],404)
    data={'name':'Invitado de prueba','attendance':'yes','companions':2,'editToken':'a'*64}
    self.assertEqual(call('POST','/api/rsvp',data,foreign=True)[0],403)
    code,rsvp,_=call('POST','/api/rsvp',data);self.assertEqual(code,200)
    data['companions']=3
    self.assertEqual(call('POST','/api/rsvp',data)[1]['reference'],rsvp['reference'])
    password=Path(temp,'ACCESO-PRIVADO.txt').read_text().split('Contraseña: ')[1].splitlines()[0]
    code,login,cookie=call('POST','/api/admin/login',{'password':password});self.assertEqual(code,200)
    code,dashboard,_=call('GET','/api/admin/dashboard',cookie=cookie)
    self.assertEqual(dashboard['totals']['confirmed'],1);self.assertEqual(dashboard['totals']['people'],4)
    image=Image.new('RGB',(200,150),'#102642');buffer=io.BytesIO();image.save(buffer,'JPEG')
    photo={'name':'Recuerdo de prueba','caption':'Una frase de prueba','consent':True,'image':base64.b64encode(buffer.getvalue()).decode()}
    self.assertEqual(call('POST','/api/photos',photo)[0],201)
    self.assertEqual(call('GET','/api/photos')[1]['photos'],[])
    photos=call('GET','/api/admin/dashboard',cookie=cookie)[1]['photos'];photo_id=photos[0]['id']
    self.assertEqual(call('GET','/media/'+photo_id+'.jpg')[0],404)
    self.assertEqual(call('GET','/media/'+photo_id+'.jpg',cookie=cookie)[0],200)
    moderation={'id':photo_id,'status':'approved'}
    self.assertEqual(call('POST','/api/admin/moderate',moderation,cookie=cookie)[0],403)
    self.assertEqual(call('POST','/api/admin/moderate',moderation,cookie=cookie,csrf=login['csrf'])[0],200)
    self.assertEqual(len(call('GET','/api/photos')[1]['photos']),1)
    self.assertEqual(call('GET','/media/'+photo_id+'.jpg')[0],200)
    moderation['status']='hidden';call('POST','/api/admin/moderate',moderation,cookie=cookie,csrf=login['csrf'])
    self.assertEqual(call('GET','/api/photos')[1]['photos'],[])
    self.assertEqual(call('GET','/media/'+photo_id+'.jpg')[0],404)
    photo['image']=base64.b64encode(b'<svg onload="alert(1)"></svg>').decode()
    self.assertEqual(call('POST','/api/photos',photo)[0],400)
    data['attendance']='no';data['companions']=0;call('POST','/api/rsvp',data)
    dashboard=call('GET','/api/admin/dashboard',cookie=cookie)[1]
    self.assertEqual(dashboard['totals']['people'],0);self.assertEqual(dashboard['totals']['declined'],1)
    call('POST','/api/admin/logout',{},cookie=cookie,csrf=login['csrf'])
    self.assertEqual(call('GET','/api/admin/dashboard',cookie=cookie)[0],401)
    code,login,cookie=call('POST','/api/admin/login',{'password':password})
    self.assertEqual(code,200)
    self.assertEqual(call('GET','/admin',cookie=cookie)[0],200)
    self.assertEqual(call('GET','/api/admin/dashboard',cookie=cookie)[0],401)
    code,login,cookie=call('POST','/api/admin/login',{'password':password})
    self.assertEqual(code,200)
    self.assertEqual(call('GET','/admin.html',cookie=cookie)[0],200)
    self.assertEqual(call('GET','/api/admin/dashboard',cookie=cookie)[0],401)
   finally:server.shutdown();server.server_close();thread.join()

if __name__=='__main__':unittest.main()
