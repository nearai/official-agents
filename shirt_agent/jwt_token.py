from os import access
import jwt.utils
import time
import math


def main():
    accessKey = {
        "signing_secret": "bzo1YStKQfjXgLRPBRPtjPFpeNHiiJjdfjSvtgpCw04", 
        "developer_id": "03924e76-6461-4635-b735-c049d2fda821",
        "key_id": "778560c4-a3d3-4cca-9698-46f0695bee39"
        }

    token = jwt.encode(
        {
            "aud": "doordash",
            "iss": accessKey["developer_id"],
            "kid": accessKey["key_id"],
            "exp": str(math.floor(time.time() + 300)),
            "iat": str(math.floor(time.time())),
        },
        jwt.utils.base64url_decode(accessKey["signing_secret"]),
        algorithm="HS256",
        headers={"dd-ver": "DD-JWT-V1"})

    print(token)

if __name__ == "__main__":
    main()
