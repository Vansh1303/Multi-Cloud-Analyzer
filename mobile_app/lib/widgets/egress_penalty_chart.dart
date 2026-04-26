import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';

class EgressPenaltyChart extends StatelessWidget {
  final Map<String, dynamic> costEstimate;

  const EgressPenaltyChart({
    super.key,
    required this.costEstimate,
  });

  @override
  Widget build(BuildContext context) {
    final providers = costEstimate.keys.toList();
    
    return AspectRatio(
      aspectRatio: 1.5,
      child: BarChart(
        BarChartData(
          alignment: BarChartAlignment.spaceAround,
          maxY: 200,
          barTouchData: BarTouchData(enabled: true),
          titlesData: FlTitlesData(
            show: true,
            bottomTitles: AxisTitles(
              sideTitles: SideTitles(
                showTitles: true,
                getTitlesWidget: (value, meta) {
                  if (value.toInt() >= 0 && value.toInt() < providers.length) {
                    return Padding(
                      padding: const EdgeInsets.only(top: 8.0),
                      child: Text(
                        providers[value.toInt()],
                        style: const TextStyle(color: Color(0xFF8B8FA3)),
                      ),
                    );
                  }
                  return const Text('');
                },
              ),
            ),
            leftTitles: AxisTitles(
              sideTitles: SideTitles(
                showTitles: true,
                reservedSize: 40,
                getTitlesWidget: (value, meta) {
                  return Text(
                    '\$${value.toInt()}',
                    style: const TextStyle(color: Color(0xFF8B8FA3), fontSize: 10),
                  );
                },
              ),
            ),
            rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
            topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          ),
          gridData: FlGridData(
            show: true,
            drawVerticalLine: false,
            getDrawingHorizontalLine: (value) => FlLine(
              color: Colors.white.withOpacity(0.08),
              strokeWidth: 1,
            ),
          ),
          borderData: FlBorderData(show: false),
          barGroups: providers.asMap().entries.map((entry) {
            final int index = entry.key;
            final String provider = entry.value;
            final double storage = costEstimate[provider]['storage']?.toDouble() ?? 0;
            final double egress = costEstimate[provider]['egress']?.toDouble() ?? 0;

            return BarChartGroupData(
              x: index,
              barRods: [
                BarChartRodData(
                  toY: storage + egress,
                  width: 32,
                  borderRadius: const BorderRadius.vertical(top: Radius.circular(4)),
                  rodStackItems: [
                    BarChartRodStackItem(0, storage, const Color(0xFF2ECC71)),
                    BarChartRodStackItem(storage, storage + egress, const Color(0xFFE74C3C)),
                  ],
                ),
              ],
            );
          }).toList(),
        ),
      ),
    );
  }
}
