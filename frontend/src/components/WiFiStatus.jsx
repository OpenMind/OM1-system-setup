import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Wifi, WifiOff, RefreshCw, Loader } from 'lucide-react';

const API_BASE = '/api';

function WiFiStatus() {
  const [wifiStatus, setWifiStatus] = useState(null);
  const [networks, setNetworks] = useState([]);
  const [initialLoading, setInitialLoading] = useState(true);
  const [loading, setLoading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [showNetworkList, setShowNetworkList] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [selectedNetwork, setSelectedNetwork] = useState(null);
  const [password, setPassword] = useState('');

  // Fetch WiFi status
  const fetchWiFiStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE}/wifi/status`);
      if (response.data.success) {
        setWifiStatus(response.data.data);
      }
    } catch (error) {
      console.error('Failed to fetch WiFi status:', error);
    } finally {
      setInitialLoading(false);
    }
  };

  // Scan for networks
  const scanNetworks = async () => {
    setScanning(true);
    try {
      const response = await axios.get(`${API_BASE}/wifi/networks`);
      if (response.data.success) {
        setNetworks(response.data.data);
        setShowNetworkList(true);
      }
    } catch (error) {
      console.error('Failed to scan networks:', error);
    } finally {
      setScanning(false);
    }
  };

  // Connect to network
  const connectToNetwork = async () => {
    if (!selectedNetwork) return;
    
    setConnecting(true);
    try {
      const response = await axios.post(`${API_BASE}/wifi/connect`, {
        ssid: selectedNetwork.ssid,
        password: password
      });
      
      if (response.data.success) {
        setSelectedNetwork(null);
        setPassword('');
        setShowNetworkList(false);
        await fetchWiFiStatus();
      } else {
        alert(response.data.message || 'Failed to connect');
      }
    } catch (error) {
      console.error('Connection failed:', error);
      alert('Failed to connect to network');
    } finally {
      setConnecting(false);
    }
  };

  // Auto-refresh status every 5 seconds
  useEffect(() => {
    fetchWiFiStatus();
    const interval = setInterval(fetchWiFiStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const getSignalIcon = (signal) => {
    if (signal >= 75) return '▂▄▆█';
    if (signal >= 50) return '▂▄▆';
    if (signal >= 25) return '▂▄';
    return '▂';
  };

  if (initialLoading) {
    return (
      <div className="bg-white rounded-2xl p-8 shadow-sm flex flex-col gap-5">
        <div className="flex justify-between items-center pb-5 border-b border-gray-200">
          <div className="flex items-center gap-4 animate-pulse">
            <div className="w-6 h-6 bg-gray-200 rounded-full"></div>
            <div>
              <div className="h-3.5 bg-gray-200 rounded w-20 mb-2"></div>
              <div className="h-3.5 bg-gray-200 rounded w-28"></div>
            </div>
          </div>
          <div className="h-10 w-28 bg-gray-200 rounded-lg animate-pulse"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl p-8 shadow-sm flex flex-col gap-5">
      <div className="flex justify-between items-center pb-5 border-b border-gray-200">
        <div className="flex items-center gap-4">
          {wifiStatus?.connected ? (
            <Wifi className="text-green-500" size={24} />
          ) : (
            <WifiOff className="text-red-500" size={24} />
          )}
          <div>
            <div className="text-sm text-slate-600 mb-1">WiFi status</div>
            <div className="text-base font-semibold text-slate-800">
              {wifiStatus?.connected ? wifiStatus.ssid : 'Not connected'}
            </div>
          </div>
        </div>
        <button 
          className="px-5 py-2.5 bg-blue-500 text-white border-none rounded-lg font-medium text-sm cursor-pointer transition-all hover:bg-blue-600 disabled:opacity-60 disabled:cursor-not-allowed flex items-center gap-2" 
          onClick={scanNetworks}
          disabled={scanning}
        >
          {scanning && <Loader className="animate-spin" size={16} />}
          Change WIFI
        </button>
      </div>

      {showNetworkList && (
        <div className="flex flex-col gap-4">
          <div className="flex justify-between items-center">
            <h3 className="text-base font-semibold text-slate-800">Available Networks</h3>
            <button 
              className="p-2 bg-transparent border-none rounded-lg cursor-pointer transition-colors hover:bg-slate-100 disabled:opacity-60 disabled:cursor-not-allowed" 
              onClick={scanNetworks}
              disabled={scanning}
            >
              <RefreshCw className={scanning ? 'animate-spin' : ''} size={16} />
            </button>
          </div>

          {networks.length === 0 ? (
            <div className="py-10 text-center text-slate-400 text-sm">
              {scanning ? 'Scanning...' : 'No networks found'}
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              {networks.map((network, index) => (
                <div 
                  key={index}
                  className={`p-4 border rounded-lg cursor-pointer transition-all ${
                    network.connected ? 'bg-green-50 border-green-200' : 
                    selectedNetwork?.ssid === network.ssid ? 'bg-blue-50 border-blue-300' : 
                    'border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                  }`}
                  onClick={() => setSelectedNetwork(network)}
                >
                  <div className="flex justify-between items-center">
                    <div className="flex-1">
                      <div className="font-medium text-slate-800 mb-1">{network.ssid}</div>
                      <div className="flex items-center gap-2 text-xs text-slate-500">
                        <span>{getSignalIcon(network.signal)}</span>
                        <span>{network.security}</span>
                      </div>
                    </div>
                    {network.connected && (
                      <span className="px-2.5 py-1 bg-green-500 text-white rounded text-xs font-medium">Connected</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {selectedNetwork && !selectedNetwork.connected && (
            <div className="flex flex-col gap-3 pt-4 border-t border-slate-200">
              <input
                type="password"
                className="w-full px-4 py-3 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder={`Password for ${selectedNetwork.ssid}`}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && connectToNetwork()}
              />
              <div className="flex gap-2">
                <button 
                  className="flex-1 px-4 py-2.5 bg-slate-100 text-slate-700 border-none rounded-lg font-medium text-sm cursor-pointer transition-colors hover:bg-slate-200"
                  onClick={() => {
                    setSelectedNetwork(null);
                    setPassword('');
                  }}
                >
                  Cancel
                </button>
                <button 
                  className="flex-1 px-4 py-2.5 bg-green-600 text-white border-none rounded-lg font-medium text-sm cursor-pointer transition-colors hover:bg-green-700 disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  onClick={connectToNetwork}
                  disabled={connecting}
                >
                  {connecting && <Loader className="animate-spin" size={16} />}
                  {connecting ? 'Connecting...' : 'Connect'}
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default WiFiStatus;
