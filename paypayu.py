import aiohttp
import datetime
import random
import os

PROXY_URL = http://qpgohwrj-JP-rotate:g7zwblzq1ekf@p.webshare.io:80
os.environ.get("PAYPAY_PROXY", None)

_UA_LIST = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
]

def _ua():
    return random.choice(_UA_LIST)


async def login(phoneNumber: str, password: str, uuid: str):
    headers = {
        'User-Agent': _ua(),
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
        'Origin': 'https://www.paypay.ne.jp',
        'Referer': 'https://www.paypay.ne.jp/app/account/sign-in',
    }
    payload = {
        "scope": "SIGN_IN",
        "client_uuid": f"{uuid}",
        "grant_type": "password",
        "username": phoneNumber,
        "password": password,
        "add_otp_prefix": True,
        "language": "ja"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://www.paypay.ne.jp/app/v1/oauth/token",
            headers=headers, json=payload, proxy=PROXY_URL
        ) as r:
            return await r.json()


async def login_otp(set_uuid, otp, otpid, otp_pre):
    headers = {
        'User-Agent': _ua(),
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
        'Origin': 'https://www.paypay.ne.jp',
        'Referer': 'https://www.paypay.ne.jp/app/account/sign-in',
    }
    payload = {
        "scope": "SIGN_IN",
        "client_uuid": f"{set_uuid}",
        "grant_type": "otp",
        "otp_prefix": str(otp_pre),
        "otp": otp,
        "otp_reference_id": otpid,
        "username_type": "MOBILE",
        "language": "ja"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://www.paypay.ne.jp/app/v1/oauth/token",
            headers=headers, json=payload, proxy=PROXY_URL
        ) as r:
            res = await r.json()
            try:
                if res["response_type"] == "ErrorResponse":
                    return "ERR"
            except Exception:
                return "OK"


async def check_link(cd: str):
    if "https://" in cd:
        cd = cd.replace("https://pay.paypay.ne.jp/", "")
    headers = {
        "Accept": "application/json, text/plain, */*",
        'User-Agent': _ua(),
        "Content-Type": "application/json"
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                f"https://www.paypay.ne.jp/app/v2/p2p-api/getP2PLinkInfo?verificationCode={cd}",
                headers=headers, proxy=PROXY_URL
            ) as r:
                r.raise_for_status()
                info = await r.json()
        except aiohttp.ClientError as e:
            print(f"check_link error: {e}")
            return False

    if info.get("header", {}).get("resultCode") != "S0000":
        return False
    if info.get("payload", {}).get("orderStatus") == "PENDING":
        return info
    return False


async def link_rev(cd: str, phoneNumber: str, password: str, uuid: str, link_password: str = None):
    if "https://" in cd:
        cd = cd.replace("https://pay.paypay.ne.jp/", "")

    base_headers = {
        "Accept": "application/json, text/plain, */*",
        'User-Agent': _ua(),
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:

        try:
            async with session.get(
                f"https://www.paypay.ne.jp/app/v2/p2p-api/getP2PLinkInfo?verificationCode={cd}",
                headers=base_headers, proxy=PROXY_URL
            ) as r:
                r.raise_for_status()
                link_info = await r.json()

            if link_info.get("payload", {}).get("orderStatus") != "PENDING":
                return False
            if link_info.get("payload", {}).get("pendingP2PInfo", {}).get("isSetPasscode") and link_password is None:
                return False
        except aiohttp.ClientError as e:
            print(f"link_info error: {e}")
            return False

        login_headers = {
            'User-Agent': _ua(),
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'Origin': 'https://www.paypay.ne.jp',
            'Referer': f'https://pay.paypay.ne.jp/{cd}',
        }
        login_payload = {
            "scope": "SIGN_IN",
            "client_uuid": f"{uuid}",
            "grant_type": "password",
            "username": phoneNumber,
            "password": password,
            "add_otp_prefix": True,
            "language": "ja"
        }
        async with session.post(
            "https://www.paypay.ne.jp/app/v1/oauth/token",
            headers=login_headers, json=login_payload, proxy=PROXY_URL
        ) as r:
            login_res = await r.json()
            try:
                login_res["access_token"]
            except Exception:
                try:
                    login_res["otp_reference_id"]
                    return "LOGINERR"
                except Exception:
                    return "LOGINERR"

        receive_payload = {
            "verificationCode": cd,
            "client_uuid": uuid,
            "requestAt": str(
                datetime.datetime.now(
                    datetime.timezone(datetime.timedelta(hours=9))
                ).strftime('%Y-%m-%dT%H:%M:%S+0900')
            ),
            "requestId": link_info["payload"]["message"]["data"]["requestId"],
            "orderId": link_info["payload"]["message"]["data"]["orderId"],
            "senderMessageId": link_info["payload"]["message"]["messageId"],
            "senderChannelUrl": link_info["payload"]["message"]["chatRoomId"],
            "iosMinimumVersion": "3.45.0",
            "androidMinimumVersion": "3.45.0"
        }
        if link_password:
            receive_payload["passcode"] = link_password

        try:
            async with session.post(
                "https://www.paypay.ne.jp/app/v2/p2p-api/acceptP2PSendMoneyLink",
                json=receive_payload, headers=base_headers, proxy=PROXY_URL
            ) as r:
                r.raise_for_status()
                res = await r.json()
                return res.get("header", {}).get("resultCode") == "S0000"
        except aiohttp.ClientError as e:
            print(f"receive error: {e}")
            return False
