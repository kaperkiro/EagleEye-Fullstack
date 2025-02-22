class RtspConfig:
    def __init__(self, username="student", password="student_pass", 
                 ip="192.168.0.93", port="554", stream_path="axis-media/media.amp"):
        self.username = username
        self.password = password
        self.ip = ip
        self.port = port
        self.stream_path = stream_path
        
    @property
    def url(self) -> str:
        return f"rtsp://{self.username}:{self.password}@{self.ip}:{self.port}/{self.stream_path}"