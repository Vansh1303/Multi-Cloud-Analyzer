import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';

class RadarChartWidget extends StatelessWidget {
  const RadarChartWidget({super.key});

  @override
  Widget build(BuildContext context) {
    // Static values representing the evaluation from Streamlit version
    return AspectRatio(
      aspectRatio: 1.2,
      child: RadarChart(
        RadarChartData(
          dataSets: [
            RadarDataSet(
              fillColor: const Color(0xFFFF9900).withOpacity(0.3),
              borderColor: const Color(0xFFFF9900),
              entryRadius: 3,
              dataEntries: [
                const RadarEntry(value: 7),
                const RadarEntry(value: 7),
                const RadarEntry(value: 9),
                const RadarEntry(value: 7),
                const RadarEntry(value: 8),
              ],
            ),
            RadarDataSet(
              fillColor: const Color(0xFF0078D4).withOpacity(0.3),
              borderColor: const Color(0xFF0078D4),
              entryRadius: 3,
              dataEntries: [
                const RadarEntry(value: 4),
                const RadarEntry(value: 4),
                const RadarEntry(value: 8),
                const RadarEntry(value: 9),
                const RadarEntry(value: 6),
              ],
            ),
            RadarDataSet(
              fillColor: const Color(0xFF4285F4).withOpacity(0.3),
              borderColor: const Color(0xFF4285F4),
              entryRadius: 3,
              dataEntries: [
                const RadarEntry(value: 9),
                const RadarEntry(value: 9),
                const RadarEntry(value: 3),
                const RadarEntry(value: 7),
                const RadarEntry(value: 5),
              ],
            ),
          ],
          radarBackgroundColor: Colors.transparent,
          borderData: FlBorderData(show: false),
          radarBorderData: const BorderSide(color: Colors.transparent),
          getTitle: (index, angle) {
            final titles = ['Upload', 'Download', 'API', 'Cost', 'Portability'];
            return RadarChartTitle(
              text: titles[index],
              angle: 0,
            );
          },
          tickCount: 5,
          ticksTextStyle: const TextStyle(color: Colors.transparent, fontSize: 10),
          tickBorderData: const BorderSide(color: Colors.white12),
          gridBorderData: const BorderSide(color: Colors.white12, width: 2),
        ),
        swapAnimationDuration: const Duration(milliseconds: 150),
        swapAnimationCurve: Curves.linear,
      ),
    );
  }
}
