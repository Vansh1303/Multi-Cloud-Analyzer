import 'package:flutter/material.dart';

class PortabilityMatrix extends StatelessWidget {
  final List<dynamic> portabilityData;

  const PortabilityMatrix({super.key, required this.portabilityData});

  @override
  Widget build(BuildContext context) {
    // Expected portabilityData shape:
    // [
    //   {"route": "AWS->Azure", "time_seconds": 35.16},
    //   {"route": "AWS->GCP", "time_seconds": 15.89},
    //   ...
    // ]
    
    final providers = ["AWS", "Azure", "GCP"];
    final int size = providers.length;

    // Convert to a 2D map for easy lookup
    Map<String, double> matrix = {};
    for (var entry in portabilityData) {
      matrix[entry['route']] = entry['time_seconds']?.toDouble() ?? 0.0;
    }

    // Find min/max to calculate colors
    double minTime = double.infinity;
    double maxTime = -double.infinity;
    for (var val in matrix.values) {
      if (val > maxTime) maxTime = val;
      if (val < minTime && val > 0) minTime = val; // Assuming self-transfer is 0
    }

    if (minTime == double.infinity) minTime = 0;
    if (maxTime == -double.infinity) maxTime = 1;

    Color getColorForTime(double time, bool isSelf) {
      if (isSelf) return const Color(0xFF262730); // Base surface color for self-transfer
      // Map time to color from white to deep red (using an interpolated color)
      double t = (time - minTime) / (maxTime - minTime).clamp(0.001, double.infinity);
      t = t.clamp(0.0, 1.0);
      return Color.lerp(Colors.white, const Color(0xFF8B0000), t)!;
    }

    return Column(
      children: [
        // Column headers
        Row(
          children: [
            const Expanded(child: SizedBox()), // Empty top-left
            ...providers.map((p) => Expanded(
              child: Center(
                child: Text(
                  p,
                  style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.white),
                ),
              ),
            )),
          ],
        ),
        const SizedBox(height: 8),
        // Rows
        ...providers.map((source) {
          return Padding(
            padding: const EdgeInsets.only(bottom: 8.0),
            child: Row(
              children: [
                // Row header
                Expanded(
                  child: Center(
                    child: Text(
                      source,
                      style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.white),
                    ),
                  ),
                ),
                // Cells
                ...providers.map((dest) {
                  final isSelf = source == dest;
                  final time = isSelf ? 0.0 : (matrix['$source->$dest'] ?? 0.0);
                  final cellColor = getColorForTime(time, isSelf);
                  final textColor = (time > (minTime + (maxTime - minTime) / 2)) ? Colors.white : Colors.black;

                  return Expanded(
                    child: AspectRatio(
                      aspectRatio: 1,
                      child: Container(
                        margin: const EdgeInsets.all(2),
                        decoration: BoxDecoration(
                          color: cellColor,
                          borderRadius: BorderRadius.circular(4),
                          border: Border.all(color: Colors.white.withOpacity(0.1)),
                        ),
                        child: Center(
                          child: Text(
                            isSelf ? '-' : time.toStringAsFixed(1),
                            style: TextStyle(
                              color: isSelf ? Colors.white54 : textColor,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ),
                    ),
                  );
                }),
              ],
            ),
          );
        }),
      ],
    );
  }
}
