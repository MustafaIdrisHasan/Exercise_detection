import 'package:flutter/material.dart';
import 'api_service.dart';
import 'package:logging/logging.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Exercise Detection',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
      ),
      home: const HomeScreen(),
    );
  }
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({Key? key}) : super(key: key);

  @override
  _HomeScreenState createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final ApiService apiService = ApiService();
  String message = '';
  bool isLoading = false;
  bool isConnected = false;
  final Logger _logger = Logger('HomeScreen');

  @override
  void initState() {
    super.initState();
    _checkConnection();
  }

  Future<void> _checkConnection() async {
    final connected = await apiService.healthCheck();
    setState(() {
      isConnected = connected;
      if (!connected) {
        message = 'Backend server is not reachable. Please start the Flask server.';
      }
    });
  }

  Future<void> startExercise(String endpoint, String exerciseName) async {
    setState(() {
      isLoading = true;
      message = 'Starting $exerciseName...';
    });

    try {
      final response = await apiService.startExercise(endpoint);
      setState(() {
        message = response['status'] ?? 'Exercise started';
        isLoading = false;
      });
      _logger.info(response.toString());
    } catch (e) {
      setState(() {
        message = 'Error: ${e.toString()}';
        isLoading = false;
      });
      _logger.severe(e.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Exercise Detection'),
        actions: [
          IconButton(
            icon: Icon(isConnected ? Icons.check_circle : Icons.error),
            color: isConnected ? Colors.green : Colors.red,
            onPressed: _checkConnection,
            tooltip: isConnected ? 'Connected' : 'Disconnected - Tap to retry',
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            // Connection Status Card
            Card(
              color: isConnected ? Colors.green.shade50 : Colors.red.shade50,
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Row(
                  children: [
                    Icon(
                      isConnected ? Icons.check_circle : Icons.error,
                      color: isConnected ? Colors.green : Colors.red,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        isConnected
                            ? 'Connected to backend server'
                            : 'Backend server offline',
                        style: TextStyle(
                          color: isConnected ? Colors.green.shade900 : Colors.red.shade900,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 32),

            // Exercise Buttons
            Expanded(
              child: GridView.count(
                crossAxisCount: 2,
                crossAxisSpacing: 16,
                mainAxisSpacing: 16,
                children: [
                  _buildExerciseCard(
                    context,
                    'Lateral Raises',
                    Icons.fitness_center,
                    Colors.blue,
                    () => startExercise('lateral_raises', 'Lateral Raises'),
                  ),
                  _buildExerciseCard(
                    context,
                    'Shoulder Press',
                    Icons.sports_gymnastics,
                    Colors.purple,
                    () => startExercise('shoulder_press', 'Shoulder Press'),
                  ),
                  _buildExerciseCard(
                    context,
                    'Crunches',
                    Icons.accessibility_new,
                    Colors.orange,
                    () => startExercise('crunches', 'Crunches'),
                  ),
                  _buildExerciseCard(
                    context,
                    'Bicep Curls',
                    Icons.sports_martial_arts,
                    Colors.teal,
                    () => startExercise('bicep_curls', 'Bicep Curls'),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 20),

            // Status Message
            if (message.isNotEmpty)
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Row(
                    children: [
                      if (isLoading)
                        const Padding(
                          padding: EdgeInsets.only(right: 12.0),
                          child: SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          ),
                        ),
                      Expanded(
                        child: Text(
                          message,
                          style: const TextStyle(fontSize: 14),
                          textAlign: TextAlign.center,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildExerciseCard(
    BuildContext context,
    String title,
    IconData icon,
    Color color,
    VoidCallback onTap,
  ) {
    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: InkWell(
        onTap: isConnected && !isLoading ? onTap : null,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            gradient: LinearGradient(
              colors: [color.shade400, color.shade600],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                icon,
                size: 48,
                color: Colors.white,
              ),
              const SizedBox(height: 12),
              Text(
                title,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
