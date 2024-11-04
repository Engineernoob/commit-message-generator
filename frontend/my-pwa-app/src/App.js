import React, { useState } from 'react';
import { TextField, Button, Typography, Paper, Box, Stack, Card, CardContent } from '@mui/material';
import ErrorIcon from '@mui/icons-material/Error';
import PersonIcon from '@mui/icons-material/Person';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

const BACKEND_URL = 'http://127.0.0.1:5000'; // Adjust this to match your backend URL

function App() {
  const [messages, setMessages] = useState([
    { type: 'system', text: 'Welcome to Commit Message Quest! 🚀\n\nAvailable commands:\n- setup [directory]: Set up a project\n- generate [type] [message]: Generate a commit message\n- clear: Clear the messages\n- help: Show available commands\n\nChoose your path and embark on your coding adventure!' }
  ]);
  const [input, setInput] = useState('');

  const handleCommand = async () => {
    if (!input.trim()) return;

    if (input.trim().toLowerCase() === 'clear') {
      // Clear command: reset messages to an empty array
      setMessages([]);
      setInput(''); // Clear the input field
      return;
    }

    setMessages((prevMessages) => [...prevMessages, { type: 'user', text: input }]);

    try {
      const [command, ...args] = input.split(' ');
      let response = '';

      if (command === 'setup') {
        const projectDir = args[0] || `${BACKEND_URL}/default-project`;
        // Setup project request
        const res = await fetch(`${BACKEND_URL}/setup`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ projectDir, createConfig: "yes" }),
        });

        if (res.ok) {
          const data = await res.json();
          response = `Setup completed: ${data.message}`;
        } else {
          response = 'Error during setup.';
        }

      } else if (command === 'generate') {
        const commitType = args[0] || 'feat';
        const customMessage = args.slice(1).join(' ') || '';

        // Send a POST request to the Flask backend to generate a commit message
        const res = await fetch(`${BACKEND_URL}/generateCommitMessage`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ commitType, customMessage }),
        });

        if (res.ok) {
          const data = await res.json();
          response = `Generated Commit Message: ${data.commitMessage}\nYou gained ${data.experience} experience and slayed ${data.enemiesSlain} enemies.`;
        } else {
          response = 'Error generating commit message.';
        }

      } else if (command === 'help') {
        response = "Commands: setup [directory], generate [type] [message], clear, help";

      } else {
        response = `Unknown command: ${command}`;
      }

      setMessages((prevMessages) => [
        ...prevMessages,
        { type: command === 'help' || command === 'generate' || command === 'setup' ? 'system' : 'error', text: response },
      ]);
    } catch (error) {
      setMessages((prevMessages) => [
        ...prevMessages,
        { type: 'error', text: `Error encountered: ${error.message}` },
      ]);
    }

    setInput('');
  };

  const getMessageIcon = (type) => {
    if (type === 'error') return <ErrorIcon color="error" />;
    if (type === 'system') return <CheckCircleIcon color="success" />;
    return <PersonIcon color="primary" />;
  };

  const getMessageColor = (type) => {
    if (type === 'error') return '#ffcccc';
    if (type === 'system') return '#ccffcc';
    return '#cce5ff';
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: 3, backgroundColor: '#1e1e1e', height: '100vh' }}>
      <Typography variant="h4" component="h1" gutterBottom style={{ color: '#ffcc00', fontFamily: 'Courier New' }}>
        Commit Message Quest
      </Typography>

      <Paper
        variant="outlined"
        sx={{
          width: '100%',
          maxWidth: 600,
          height: 400,
          overflowY: 'auto',
          padding: 2,
          marginBottom: 2,
          backgroundColor: '#333',
          borderRadius: 2,
          boxShadow: '0px 4px 12px rgba(0, 0, 0, 0.5)',
        }}
      >
        <Stack spacing={2}>
          {messages.map((msg, index) => (
            <Card
              key={index}
              variant="outlined"
              sx={{
                backgroundColor: getMessageColor(msg.type),
                display: 'flex',
                alignItems: 'center',
                padding: 1,
                borderRadius: 1,
                margin: '5px 0',
              }}
            >
              <CardContent sx={{ display: 'flex', alignItems: 'center', padding: 1 }}>
                <Box sx={{ marginRight: 1 }}>{getMessageIcon(msg.type)}</Box>
                <Typography sx={{ color: '#333', fontFamily: 'Courier New' }}>{msg.text}</Typography>
              </CardContent>
            </Card>
          ))}
        </Stack>
      </Paper>

      <TextField
        label="Type a command"
        placeholder="e.g., setup /path/to/project, generate feat Add feature, clear"
        variant="outlined"
        fullWidth
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && handleCommand()}
        sx={{ maxWidth: 600, marginBottom: 2, input: { color: '#e0e0e0' }, backgroundColor: '#444', borderRadius: 1 }}
        InputLabelProps={{
          style: { color: '#e0e0e0' },
        }}
      />
      
      <Button
        variant="contained"
        color="primary"
        onClick={handleCommand}
        sx={{ maxWidth: 600, fontSize: '1rem', backgroundColor: '#ffcc00', '&:hover': { backgroundColor: '#ffb300' } }}
      >
        Execute Command
      </Button>
    </Box>
  );
}

export default App;
