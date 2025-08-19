# UDP Listening Issue Solution

## Problem Description

The issue you encountered is: The UDP test tool keeps pushing data to port 14550, but the service is not listening to messages. When monitoring the port with packet capture tool `udp.port == 14550`, data is found being pushed.

## Root Cause Analysis

After code analysis, the following issues were discovered:

1. **Port Configuration Mismatch**:
   - UDP test tool sends to port `14550`
   - But MAVLink service defaults to TCP port `5760`
   - UDP receiver listens on port `14550`, but is not automatically started when the application starts

2. **Service Startup Issue**:
   - Main application `main.py` does not automatically start UDP receiver
   - MAVLink service starts TCP receiver, not UDP receiver
   - UDP receiver needs to be started manually

3. **Protocol Mismatch**:
   - Test tool sends UDP data to port 14550
   - Service starts TCP listener on port 5760

## Solution

### 1. Modify Application Startup Logic

Added application startup and shutdown event handlers in `src/app/main.py`:

```python
@app.on_event("startup")
async def startup_event():
    """Application startup event handler"""
    print("Starting UDP receiver...")
    try:
        await start_udp_receiver()
        print("UDP receiver started successfully, listening on port 14550")
    except Exception as e:
        print(f"Failed to start UDP receiver: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event handler"""
    print("Stopping UDP receiver...")
    try:
        await stop_udp_receiver()
        print("UDP receiver stopped")
    except Exception as e:
        print(f"Failed to stop UDP receiver: {e}")
```

### 2. Add UDP Status Query API

Added UDP receiver status query endpoints in `src/app/api/mavlink.py`:

- `GET /api/v1/mavlink/udp/status` - Get UDP receiver status
- `GET /api/v1/mavlink/udp/messages` - Get UDP messages
- `GET /api/v1/mavlink/udp/sessions` - Get UDP sessions

### 3. Create Test Tool

Created `test_udp_receiver.py` test script to verify UDP receiver functionality.

## Usage Instructions

### 1. Restart Service

```bash
# Stop current service (if running)
# Then restart
python start.py
```

### 2. Verify UDP Receiver Status

Access API endpoint to check UDP receiver status:
```bash
curl http://localhost:8000/api/v1/mavlink/udp/status
```

### 3. Use Test Tool

Run UDP receiver test tool:
```bash
python test_udp_receiver.py
```

### 4. Start UDP Test Client

Run UDP test tool in another terminal:
```bash
python test_udp_client.py
```

Select option 3 for continuous sending.

### 5. Monitor Message Reception

Use test tool monitoring function or directly access API:
```bash
curl http://localhost:8000/api/v1/mavlink/udp/messages?limit=10
```

## Verification Steps

1. **Check Service Startup Logs**:
   - Should see "UDP receiver started successfully, listening on port 14550" message

2. **Check UDP Receiver Status**:
   - `is_running` should be `true`
   - `port` should be `14550`

3. **Send Test Data**:
   - Use UDP test tool to send data
   - Check if messages are received

4. **View Received Messages**:
   - View received messages through API or test tool

## Port Configuration

- **UDP Receiver**: Port `14550` (for receiving UDP MAVLink data)
- **TCP Receiver**: Port `5760` (for receiving TCP MAVLink data)
- **Web API**: Port `8000` (for HTTP API access)

## Troubleshooting

If UDP messages still cannot be received:

1. **Check Firewall Settings**: Ensure port 14550 is not blocked by firewall
2. **Check Port Usage**: Ensure port 14550 is not occupied by other programs
3. **Check Network Configuration**: Ensure UDP test tool sends to correct IP address
4. **Check Logs**: Check application startup logs and error messages

## API Endpoints

### UDP Related Endpoints

- `GET /api/v1/mavlink/udp/status` - UDP receiver status
- `GET /api/v1/mavlink/udp/messages?limit=100` - UDP message list
- `GET /api/v1/mavlink/udp/sessions` - UDP session list

### TCP Related Endpoints

- `GET /api/v1/mavlink/receiver/status` - TCP receiver status
- `GET /api/v1/mavlink/messages` - TCP message list
- `GET /api/v1/mavlink/sessions` - TCP session list

Now the UDP receiver should be able to normally receive data from port 14550!
