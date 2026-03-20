## Implementation

### Phase 2

#### What
Adds initial Python version script and Dockerfile.

#### How to test

Build the image:
```bash
docker build -t hivebox:v0.0.1 .
```

Run the container:
```bash
docker run hivebox:v0.0.1
```

Expected output:
```
v0.0.1
```