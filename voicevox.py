import requests
import json
import time

def audio_query(text, speaker, max_retry, url_voicevox):
    # 音声合成用のクエリを作成する
    query_payload = {"text": text, "speaker": speaker}
    for query_i in range(max_retry):
        r = requests.post(url_voicevox + "/audio_query", 
                        params=query_payload, timeout=(10.0, 300.0))
        if r.status_code == 200:
            query_data = r.json()
            break
        time.sleep(0.5)
    else:
        raise ConnectionError("リトライ回数が上限に到達しました。 audio_query : ", "/", text[:30], r.text)
    return query_data

def synthesis(speaker, query_data,max_retry, url_voicevox):
    synth_payload = {"speaker": speaker}
    for synth_i in range(max_retry):
        r = requests.post(url_voicevox + "/synthesis", params=synth_payload, 
                          data=json.dumps(query_data), timeout=(10.0, 300.0))
        if r.status_code == 200:
            #音声ファイルを返す
            return r.content
        time.sleep(0.5)
    else:
        raise ConnectionError("音声エラー：リトライ回数が上限に到達しました。 synthesis : ", r)

def text_to_speech(text, url_voicevox, speaker=8, max_retry=20):
    if text==False:
        text="エラーが発生したのだ"
    # audio_query
    query_data = audio_query(text,speaker,max_retry,url_voicevox)
    # synthesis
    voice_data=synthesis(speaker,query_data,max_retry,url_voicevox)
    return voice_data

def dummy_wakeup(url_voicevox):
    query_payload = {"text": "ダミー", "speaker": 8}
    max_retry = 10
    for query_i in range(max_retry):
        r = requests.post(url_voicevox + "/audio_query", params=query_payload, timeout=(10.0, 300.0))
        if r.status_code == 200:
            query_data = r.json()
            break
        time.sleep(0.1)