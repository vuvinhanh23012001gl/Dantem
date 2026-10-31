import multiprocessing
import uvicorn
from app.main import app
import torch  # pyright: ignore[reportMissingImports]
import torch.distributed  # pyright: ignore[reportMissingImports]
import torch.distributed.rpc  # pyright: ignore[reportMissingImports]
import torchvision  # pyright: ignore[reportMissingImports]
import torchvision.ops  # pyright: ignore[reportMissingImports]

if __name__ == "__main__":
    multiprocessing.freeze_support()
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=False,
        ws_ping_interval=None
    )
