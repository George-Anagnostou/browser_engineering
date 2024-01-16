import socket
import ssl

class URL:
    def __init__(self, url):
        self.scheme, url = url.split("://", 1)
        self.view_source = False
        if ":" in self.scheme:
            string, self.scheme = self.scheme.split(":", 1)
            if string == "view-source":
                self.view_source = True
        assert self.scheme in ["http", "https", "file", "data"]
        if self.scheme == "http":
            self.port = 80
        elif self.scheme == "https":
            self.port = 443

        if "/" not in url:
            url = url + "/"
        self.host, url = url.split("/", 1)

        if self.host == "/" and self.scheme == "file":
            # self.host = "127.0.0.1"
            self.host = "localhost"
        if ":" in self.host:
            self.host, port = self.host.split(":", 1)
            self.port = int(port)

        self.path = "/" + url

    def request(self):
        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )

        if self.scheme == "file":
            with open(self.path, "r") as f:
                body = f.read()
                return body

        if self.scheme == "data":
            header, body = self.path.split(",", 1)
            return body

        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)

        s.connect((self.host, self.port))
        connection_string = f"GET {self.path} HTTP/1.1\r\n".format(self.path) + \
                "Host: {}\r\n".format(self.host) + \
                "Connection: close" + \
                "User-Agent: snake-eyes/0.1 (custom)\r\n\r\n"
        s.send((connection_string).encode("utf8"))

        response = s.makefile("r", encoding="utf8", newline="\r\n")
        statusline = response.readline()
        version, status, explanation = statusline.split(" ", 2)

        response_headers = {}
        while True:
            line = response.readline()
            if line == "\r\n": break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()
        assert "transfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers

        charset = "utf-8"
        for header in response_headers:
            if header == "content-type" and ";" in response_headers[header]:
                format, charset = response_headers["content-type"].split(";", 1)
                _, charset = charset.split("=", 1)

        body = response.read()
        print(charset)
        body.encode(charset)
        s.close()

        return body

    def show(url):
        entities = {
            "&lt;": "<",
            "&gt;": ">",
            "&copy;": "©",
            "&ndash;": "–",
            "&amp;": "&",
        }

        body_string = ""
        if not url.view_source:
            in_tag = False
            for c in url.request():
                if c == "<":
                    in_tag = True
                elif c == ">":
                    in_tag = False
                elif not in_tag:
                    body_string += c
            for entity in entities.keys():
                body_string = body_string.replace(entity, entities[entity])
        else:
            body_string = url.request()


        print(body_string)

    def load(url):
        # body = url.request()
        # URL.show(body)
        URL.show(url)

if __name__ == "__main__":
    import sys
    import os
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = "file://"
        path += os.path.abspath("sample.html")

    URL.load(URL(path))
