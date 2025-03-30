import React, { useState, useEffect, useRef, useContext } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { AppContext } from '../context/AppContext';
import { FaPaperPlane, FaImage, FaSpinner } from 'react-icons/fa';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';

function ChatView() {
  const { conversationId } = useParams();
  const { 
    apiService, 
    defaultModel, 
    useRag 
  } = useContext(AppContext);
  const navigate = useNavigate();
  
  // Chat state
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [error, setError] = useState(null);
  
  // WebSocket state
  const [ws, setWs] = useState(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamedResponse, setStreamedResponse] = useState('');
  
  // References
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  
  // Fetch conversation if conversationId is provided
  useEffect(() => {
    if (conversationId) {
      fetchConversation();
    } else {
      // Reset for new conversation
      setMessages([]);
      setStreamedResponse('');
    }
    
    // Clean up WebSocket connection when component unmounts
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [conversationId]);
  
  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages, streamedResponse]);
  
  const fetchConversation = async () => {
    try {
      setIsLoading(true);
      const data = await apiService.getConversation(conversationId);
      setMessages(data.messages);
      setIsLoading(false);
    } catch (error) {
      setError(`Error loading conversation: ${error.message}`);
      setIsLoading(false);
    }
  };
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  const handleSendMessage = async () => {
    if (!inputMessage.trim() && !imageFile) return;
    
    try {
      setIsLoading(true);
      setError(null);
      
      const userMessage = inputMessage;
      setInputMessage('');
      
      // Add user message to UI immediately
      const newUserMessage = {
        role: 'user',
        content: imageFile ? `[Message with image] ${userMessage}` : userMessage,
        timestamp: new Date().toISOString()
      };
      
      setMessages(prev => [...prev, newUserMessage]);
      
      let response;
      
      if (imageFile) {
        // Upload image first
        const uploadResult = await apiService.uploadImage(imageFile);
        
        // Send message with image
        response = await apiService.sendMessageWithImage(
          userMessage,
          uploadResult.path,
          conversationId,
          defaultModel,
          useRag
        );
        
        // Clear image
        setImageFile(null);
        setImagePreview(null);
      } else {
        // Regular text message
        response = await apiService.sendMessage(
          userMessage,
          conversationId,
          defaultModel,
          useRag
        );
      }
      
      // If this is a new conversation, update URL
      if (!conversationId) {
        navigate(`/chat/${response.conversation_id}`);
      }
      
      // Add assistant response
      const newAssistantMessage = {
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toISOString()
      };
      
      setMessages(prev => [...prev, newAssistantMessage]);
      setIsLoading(false);
    } catch (error) {
      setError(`Error sending message: ${error.message}`);
      setIsLoading(false);
    }
  };
  
  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    // Set file for upload
    setImageFile(file);
    
    // Create preview
    const reader = new FileReader();
    reader.onload = (e) => {
      setImagePreview(e.target.result);
    };
    reader.readAsDataURL(file);
  };
  
  const removeImage = () => {
    setImageFile(null);
    setImagePreview(null);
  };
  
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };
  
  