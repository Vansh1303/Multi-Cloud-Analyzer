import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';
import '../widgets/hero_metrics_card.dart';
import '../widgets/egress_penalty_chart.dart';
import '../widgets/download_speed_chart.dart';
import '../widgets/radar_chart_widget.dart';
import '../widgets/portability_matrix.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  final ApiService _apiService = ApiService();
  final AuthService _authService = AuthService();

  Map<String, dynamic>? _telemetryData;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadTelemetry();
  }

  Future<void> _loadTelemetry() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final data = await _apiService.fetchTelemetry();
      setState(() {
        _telemetryData = data;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  Future<void> _runBenchmark() async {
    try {
      final token = await _authService.getIdToken();
      if (token == null) throw Exception("User not authenticated.");
      
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Triggering benchmark...')),
      );

      final success = await _apiService.runBenchmark(token);
      if (success) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Benchmark queued successfully! Pull to refresh later.'),
            backgroundColor: Colors.green,
          ),
        );
      } else {
        throw Exception("Failed to queue benchmark.");
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(e.toString()),
          backgroundColor: Colors.redAccent,
        ),
      );
    }
  }

  void _signOut() async {
    await _authService.signOut();
    if (mounted) {
      Navigator.pushReplacementNamed(context, '/login');
    }
  }

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 4,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Dashboard', style: TextStyle(fontWeight: FontWeight.bold)),
          backgroundColor: const Color(0xFF13151C),
          actions: [
            IconButton(
              icon: const Icon(Icons.refresh),
              onPressed: _loadTelemetry,
            ),
            IconButton(
              icon: const Icon(Icons.logout),
              onPressed: _signOut,
            ),
          ],
          bottom: const TabBar(
            isScrollable: true,
            indicatorColor: Color(0xFF0068C9),
            labelColor: Color(0xFF0068C9),
            unselectedLabelColor: Color(0xFF8B8FA3),
            tabs: [
              Tab(text: '📊 Performance & Radar'),
              Tab(text: '💰 Lock-In Analysis'),
              Tab(text: '🔄 Portability Matrix'),
              Tab(text: '🗄️ Data Explorer'),
            ],
          ),
        ),
        floatingActionButton: FloatingActionButton.extended(
          onPressed: _runBenchmark,
          backgroundColor: const Color(0xFF0068C9),
          icon: const Icon(Icons.play_arrow, color: Colors.white),
          label: const Text('Run Benchmark', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        ),
        body: _buildBody(),
      ),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 48, color: Colors.redAccent),
            const SizedBox(height: 16),
            Text('Error: $_error', textAlign: TextAlign.center),
            const SizedBox(height: 16),
            ElevatedButton(onPressed: _loadTelemetry, child: const Text('Retry')),
          ],
        ),
      );
    }
    if (_telemetryData == null) {
      return const Center(child: Text('No data available.'));
    }

    return TabBarView(
      children: [
        _buildPerformanceTab(),
        _buildLockInTab(),
        _buildPortabilityTab(),
        _buildDataExplorerTab(),
      ],
    );
  }

  Widget _buildPerformanceTab() {
    final data = _telemetryData!;
    final uploadSpeeds = data['upload_speeds'] as Map<String, dynamic>;
    final downloadSpeeds = data['download_speeds'] as Map<String, dynamic>;
    final latency = data['latency_ms'] as Map<String, dynamic>;
    final providers = (data['providers'] as List<dynamic>).cast<String>();

    String fastestProvider = '';
    double maxSpeed = 0;
    uploadSpeeds.forEach((k, v) {
      if (v > maxSpeed) {
        maxSpeed = v.toDouble();
        fastestProvider = k;
      }
    });

    String lowestLatencyProvider = '';
    double minLatency = double.infinity;
    latency.forEach((k, v) {
      double avgLat = ((v['Metadata'] ?? 0) + (v['List'] ?? 0) + (v['Delete'] ?? 0)) / 3;
      if (avgLat < minLatency) {
        minLatency = avgLat;
        lowestLatencyProvider = k;
      }
    });

    return RefreshIndicator(
      onRefresh: _loadTelemetry,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          HeroMetricsCard(
            title: 'Fastest Upload',
            value: fastestProvider,
            subtitle: '${maxSpeed.toStringAsFixed(1)} MB/s',
            icon: Icons.rocket_launch,
            iconColor: const Color(0xFF0068C9),
          ),
          HeroMetricsCard(
            title: 'Lowest API Latency',
            value: lowestLatencyProvider,
            subtitle: '${minLatency.toStringAsFixed(0)} ms avg',
            icon: Icons.bolt,
            iconColor: const Color(0xFF2ECC71),
          ),
          const HeroMetricsCard(
            title: 'Highest Lock-In Risk',
            value: 'GCP',
            subtitle: 'Slower Egress & High Cost',
            icon: Icons.warning_amber_rounded,
            iconColor: Color(0xFFE74C3C),
          ),
          const SizedBox(height: 32),
          
          // Side-by-side or stacked charts using Wrap or Column
          LayoutBuilder(
            builder: (context, constraints) {
              if (constraints.maxWidth > 600) {
                return Row(
                  children: [
                    Expanded(
                      child: _buildChartContainer('Upload Speed (Ingress)', _buildUploadChart(providers, uploadSpeeds)),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: _buildChartContainer('Download Speed (Egress)', DownloadSpeedChart(providers: providers, downloadSpeeds: downloadSpeeds)),
                    ),
                  ],
                );
              } else {
                return Column(
                  children: [
                    _buildChartContainer('Upload Speed (Ingress)', _buildUploadChart(providers, uploadSpeeds)),
                    const SizedBox(height: 16),
                    _buildChartContainer('Download Speed (Egress)', DownloadSpeedChart(providers: providers, downloadSpeeds: downloadSpeeds)),
                  ],
                );
              }
            },
          ),
          
          const SizedBox(height: 32),
          _buildChartContainer('Overall Provider Assessment', const RadarChartWidget()),
          const SizedBox(height: 80),
        ],
      ),
    );
  }

  Widget _buildLockInTab() {
    final data = _telemetryData!;
    final costEstimate = data['cost_estimate'] as Map<String, dynamic>;

    return RefreshIndicator(
      onRefresh: _loadTelemetry,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text(
            'Interactive Cost & Egress Simulator',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
          ),
          const SizedBox(height: 8),
          const Text(
            'Cloud providers make ingress free, but charge steep egress fees. This chart shows estimated monthly cost for 1 TB storage + 1 TB egress.',
            style: TextStyle(color: Color(0xFF8B8FA3)),
          ),
          const SizedBox(height: 24),
          _buildChartContainer('Egress Penalty & Storage Cost', EgressPenaltyChart(costEstimate: costEstimate)),
          const SizedBox(height: 80),
        ],
      ),
    );
  }

  Widget _buildPortabilityTab() {
    final data = _telemetryData!;
    final portability = data['portability'] as List<dynamic>;

    return RefreshIndicator(
      onRefresh: _loadTelemetry,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text(
            'Cross-Cloud Transfer Friction',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
          ),
          const SizedBox(height: 8),
          const Text(
            'Visualizing the transfer latency (in seconds) when moving data directly between cloud environments.',
            style: TextStyle(color: Color(0xFF8B8FA3)),
          ),
          const SizedBox(height: 24),
          _buildChartContainer('Portability Matrix', PortabilityMatrix(portabilityData: portability)),
          const SizedBox(height: 80),
        ],
      ),
    );
  }

  Widget _buildDataExplorerTab() {
    final data = _telemetryData!;
    final uploadSpeeds = data['upload_speeds'] as Map<String, dynamic>;
    final downloadSpeeds = data['download_speeds'] as Map<String, dynamic>;
    final providers = (data['providers'] as List<dynamic>).cast<String>();

    return RefreshIndicator(
      onRefresh: _loadTelemetry,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text(
            'Sanitized Benchmark Telemetry',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
          ),
          const SizedBox(height: 16),
          Container(
            decoration: BoxDecoration(
              color: const Color(0xFF262730),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.white.withOpacity(0.04)),
            ),
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: DataTable(
                headingTextStyle: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                dataTextStyle: const TextStyle(color: Color(0xFFFAFAFA)),
                columns: const [
                  DataColumn(label: Text('Provider')),
                  DataColumn(label: Text('Upload (MB/s)')),
                  DataColumn(label: Text('Download (MB/s)')),
                ],
                rows: providers.map((p) {
                  return DataRow(cells: [
                    DataCell(Text(p, style: const TextStyle(fontWeight: FontWeight.bold))),
                    DataCell(Text('${uploadSpeeds[p]}')),
                    DataCell(Text('${downloadSpeeds[p]}')),
                  ]);
                }).toList(),
              ),
            ),
          ),
          const SizedBox(height: 80),
        ],
      ),
    );
  }

  Widget _buildChartContainer(String title, Widget chartWidget) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF262730),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white.withOpacity(0.04)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
          ),
          const SizedBox(height: 16),
          chartWidget,
        ],
      ),
    );
  }

  Widget _buildUploadChart(List<String> providers, Map<String, dynamic> uploadSpeeds) {
    return AspectRatio(
      aspectRatio: 1.2,
      child: BarChart(
        BarChartData(
          alignment: BarChartAlignment.spaceAround,
          maxY: 15,
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
                    '${value.toInt()}',
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
            final double speed = uploadSpeeds[provider]?.toDouble() ?? 0;
            
            Color barColor = const Color(0xFF0068C9);
            if (provider == 'AWS') barColor = const Color(0xFFFF9900);
            if (provider == 'Azure') barColor = const Color(0xFF0078D4);
            if (provider == 'GCP') barColor = const Color(0xFF4285F4);

            return BarChartGroupData(
              x: index,
              barRods: [
                BarChartRodData(
                  toY: speed,
                  width: 32,
                  color: barColor,
                  borderRadius: const BorderRadius.vertical(top: Radius.circular(4)),
                ),
              ],
            );
          }).toList(),
        ),
      ),
    );
  }
}
