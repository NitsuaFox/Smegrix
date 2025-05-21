# Performance Optimization Guide

This guide outlines the performance optimizations implemented to improve responsiveness on resource-constrained devices like the Raspberry Pi.

## Key Performance Issues Addressed

The application was experiencing significant performance issues on the Raspberry Pi, with display updates taking much longer than the target 50ms interval. This resulted in warnings like:

```
[20:34:33.397] [PERF_WARNING] Display update took 173.50ms, exceeding interval of 50.00ms.
```

These delays cause visual stuttering and reduced responsiveness.

## Optimization Components

### 1. Performance Monitoring and Optimization System

The following files were added to implement performance monitoring:

- **performance_optimizer.py**: Core performance tracking and optimization system
- **performance_utils.py**: Raspberry Pi specific optimizations and system monitoring
- **templates/performance.html**: Web interface for monitoring and adjusting performance settings

### 2. Key Features

#### Adaptive Frame Rate
- Automatically adjusts update frequency based on device performance
- Can skip frames when processing is too slow to catch up

#### System Monitoring
- CPU and memory usage tracking
- CPU temperature monitoring (Raspberry Pi)
- Real-time performance metrics

#### Configurable Settings
- Update frequency control
- Animation enabling/disabling
- Frame skipping threshold control
- Logging minimization

#### Raspberry Pi Specific Optimizations
- GPU memory allocation recommendations
- CPU governor settings
- HDMI and overscan optimizations

## Using the Performance Tools

### Web Interface

Access the performance dashboard at:
```
http://your-device-ip:5001/performance
```

This dashboard allows you to:
1. Monitor system resources in real-time
2. View performance metrics and bottlenecks 
3. Adjust optimization settings

### Raspberry Pi System Optimizations

For Raspberry Pi users, an optimization script is created at `optimize_raspberry_pi.sh` which can be run with:

```bash
sudo bash optimize_raspberry_pi.sh
```

This script optimizes:
- GPU memory allocation
- Disables overscan
- Disables HDMI blanking
- Optionally disables audio to save resources
- Sets CPU governor to "performance"

## Performance Tuning Tips

1. **Increase Update Interval**: The most effective way to improve performance is to increase the update interval (reduce refresh rate).

2. **Enable Frame Skipping**: Enable the "Skip Frames When Slow" option to allow the system to skip rendering frames when it falls behind.

3. **Minimize Logging**: Reduce logging overhead by enabling the "Minimize Logging" option.

4. **Raspberry Pi Specific**:
   - Ensure your Raspberry Pi has adequate cooling
   - Set GPU memory appropriately (128MB is sufficient for this application)
   - Consider overclocking if your cooling solution is adequate

5. **Monitoring Performance**:
   - Watch the "Performance Threshold Exceeded" percentage
   - Monitor the average time for display updates
   - Check CPU temperature to ensure it's not throttling due to overheating

## Debugging

The performance tools log detailed timing information that can help identify specific bottlenecks:

```
[PERF] update_display_content: 87.53ms (SLOW)
[PERF_STATS] FPS: 9.7, Frames: 97, Skipped: 3 (3.1%)
```

These logs help identify which components are causing performance problems.

## Troubleshooting

If you encounter performance issues:

1. Check CPU temperature - the Pi will throttle when overheating
2. Increase the update interval multiplier 
3. Enable frame skipping
4. Verify the CPU governor is set to "performance"
5. Close other applications running on the device

For persistent issues, check the `performance_log.json` file for detailed timing data that can help identify bottlenecks. 