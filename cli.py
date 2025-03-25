#!/usr/bin/env python3
import argparse
import sys
import os
from eom import EdgeOMatic

def main():
    parser = argparse.ArgumentParser(description="EdgeOMatic API server")
    parser.add_argument("--listen-addr", default="0.0.0.0", help="Address to listen on (default: 0.0.0.0)")
    parser.add_argument("--listen-port", type=int, default=8000, help="Port to listen on (default: 8000)")
    parser.add_argument("--dev-addr", required=True, help="EdgeOMatic device address")
    parser.add_argument("--dev-port", type=int, default=80, help="EdgeOMatic device port (default: 80)")
    
    args = parser.parse_args()
    
    # Set environment variables that will be read by rest.py
    os.environ["EOM_DEV_ADDR"] = args.dev_addr
    os.environ["EOM_DEV_PORT"] = str(args.dev_port)
    
    # Run the app with our parameters
    import uvicorn
    print(f"Starting server on {args.listen_addr}:{args.listen_port}")
    print(f"Connecting to EdgeOMatic at {args.dev_addr}:{args.dev_port}")
    
    # Import the app from rest but only after setting the environment variables
    from rest import app
    
    uvicorn.run(
        app,
        host=args.listen_addr,
        port=args.listen_port,
    )

if __name__ == "__main__":
    main() 