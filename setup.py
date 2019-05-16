from setuptools import setup

setup(
    name="cameraWatcher",
    version="0.1.0",
    description="Watches a given stream and reports to a backend service",
    author="Nicholas Fitton",
    author_email="githubcamera@nfitton.com",
    url="https://github.com/NickFitton/Intelligent-CCTV_camera",
    packages=["src"],
    install_requires=[
        "numpy>=1.15.1",
        "requests>=2.20.0",
        # "picamera"
        # "black>=18.9b0",
        # "opencv-python==4.1.0",
    ],
)
