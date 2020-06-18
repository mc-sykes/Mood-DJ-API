import subprocess
import json
import pickle

def check():
    #time.sleep(10)
    print("What's up!")
    
def getToken(code, name, ip):
    result = subprocess.run(['curl -H "Authorization: Basic MWM1YjQ5NWVkMzY0NGI0Yjk0ZDdiNzFjNjEzNTY0ZTg6OTY2YTk2ZmM3NWEyNDk1N2IwMDJjZTU4YjRlNzg1Nzg=" -d grant_type=authorization_code -d code=' + code + ' -d redirect_uri=http://'+ip+':5000/api/push_button https://accounts.spotify.com/api/token'], shell=True, stdout=subprocess.PIPE)
    
    output = result.stdout.decode('utf-8')
    output = json.loads(output)
    aToken = output['access_token']
    rToken = output['refresh_token']
    
    tokens = [{'access': aToken, 'refresh': rToken}]
    
    with open(name+'_tokens.data', 'wb') as filehandle:
        pickle.dump(tokens, filehandle)
        
    result2 = subprocess.run(['curl -H "Authorization: Bearer ' + aToken + '" https://api.spotify.com/v1/me'], shell=True, stdout=subprocess.PIPE)
    output2 = result2.stdout.decode('utf-8')
    output2 = json.loads(output2)
    print(output2)
    return output2['display_name']
    
def refresh(rToken):
    result = subprocess.run(['curl -H "Authorization: Basic MWM1YjQ5NWVkMzY0NGI0Yjk0ZDdiNzFjNjEzNTY0ZTg6OTY2YTk2ZmM3NWEyNDk1N2IwMDJjZTU4YjRlNzg1Nzg=" -d grant_type=refresh_token -d refresh_token='
                              + rToken + ' https://accounts.spotify.com/api/token'], shell=True, stdout=subprocess.PIPE)
    output = result.stdout.decode('utf-8')
    output = json.loads(output)
    return output['access_token']
    
    
    