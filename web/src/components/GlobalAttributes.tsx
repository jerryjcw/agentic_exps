import React, { useState, useEffect } from 'react';
import { Plus, X, Settings } from 'lucide-react';

interface GlobalAttributesProps {
  attributes: Record<string, string>;
  onChange: (attributes: Record<string, string>) => void;
}

interface AttributePair {
  id: string;
  key: string;
  value: string;
}

const GlobalAttributes: React.FC<GlobalAttributesProps> = ({ attributes, onChange }) => {
  const [attributePairs, setAttributePairs] = useState<AttributePair[]>([]);

  // Initialize pairs only once when component mounts
  useEffect(() => {
    const pairs = Object.entries(attributes).map(([key, value], index) => ({
      id: `attr-${index}-${Date.now()}`,
      key,
      value
    }));

    // If no attributes, add one empty pair
    if (pairs.length === 0) {
      pairs.push({
        id: `attr-empty-${Date.now()}`,
        key: '',
        value: ''
      });
    }

    setAttributePairs(pairs);
  }, []); // Empty dependency array - run only on mount

  // Convert array of pairs back to attributes object and notify parent
  const updateAttributes = (pairs: AttributePair[]) => {
    const newAttributes: Record<string, string> = {};
    pairs.forEach(pair => {
      if (pair.key.trim() && pair.value.trim()) {
        newAttributes[pair.key.trim()] = pair.value.trim();
      }
    });
    onChange(newAttributes);
  };

  const handleKeyChange = (id: string, newKey: string) => {
    const updatedPairs = attributePairs.map(pair =>
      pair.id === id ? { ...pair, key: newKey } : pair
    );
    setAttributePairs(updatedPairs);
    updateAttributes(updatedPairs);
  };

  const handleValueChange = (id: string, newValue: string) => {
    const updatedPairs = attributePairs.map(pair =>
      pair.id === id ? { ...pair, value: newValue } : pair
    );
    setAttributePairs(updatedPairs);
    updateAttributes(updatedPairs);
  };

  const addAttribute = () => {
    const newPair: AttributePair = {
      id: `attr-${Date.now()}`,
      key: '',
      value: ''
    };
    const updatedPairs = [...attributePairs, newPair];
    setAttributePairs(updatedPairs);
  };

  const removeAttribute = (id: string) => {
    if (attributePairs.length <= 1) {
      // Always keep at least one pair, but make it empty
      const updatedPairs = [{
        id: `attr-empty-${Date.now()}`,
        key: '',
        value: ''
      }];
      setAttributePairs(updatedPairs);
      updateAttributes(updatedPairs);
    } else {
      const updatedPairs = attributePairs.filter(pair => pair.id !== id);
      setAttributePairs(updatedPairs);
      updateAttributes(updatedPairs);
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg" style={{ padding: '3%' }}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <div className="w-10 h-10 bg-gradient-to-r from-orange-500 to-red-500 rounded-lg flex items-center justify-center mr-3">
            <Settings className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Global Attributes</h2>
            <p className="text-sm text-gray-500">Define template variables for reuse</p>
          </div>
        </div>
        <div className="px-3 py-1 bg-orange-100 text-orange-800 rounded-full text-sm font-medium">
          {Object.keys(attributes).length} attribute{Object.keys(attributes).length !== 1 ? 's' : ''}
        </div>
      </div>

      <div className="space-y-4">
        {attributePairs.map((pair) => (
          <div key={pair.id} className="flex items-center" style={{ margin: '0 1rem 0 0' }}>
            <div className="flex-1 mr-8">
              <input
                type="text"
                placeholder="Attribute name (e.g., company)"
                value={pair.key}
                onChange={(e) => handleKeyChange(pair.id, e.target.value)}
                className="w-full p-4 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-gray-50 text-sm leading-relaxed transition-all duration-200 hover:border-gray-400"
              />
            </div>

            <div className="text-gray-500 font-mono text-lg font-bold mx-8" style={{ margin: '0 1rem 0 1rem' }}>=</div>

            <div className="flex-1 ml-8 mr-8" style={{ margin: '0 1rem 0 0' }}>
              <input
                type="text"
                placeholder="Attribute value (e.g., Walmart)"
                value={pair.value}
                onChange={(e) => handleValueChange(pair.id, e.target.value)}
                className="w-full p-4 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-gray-50 text-sm leading-relaxed transition-all duration-200 hover:border-gray-400"
              />
            </div>

            <button
              onClick={() => removeAttribute(pair.id)}
              className="p-3 text-red-500 hover:text-red-700 hover:bg-red-50 rounded-xl transition-all duration-200 ml-4"
              title="Remove attribute"
            >
              <X size={18} />
            </button>
          </div>
        ))}

        <div className="flex justify-center pt-2" style={{ margin: '1rem 1rem 0 0' }}>
          <button
            onClick={addAttribute}
            className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-xl hover:from-orange-600 hover:to-red-600 transition-all duration-200 shadow-md hover:shadow-lg font-medium"
          >
            <Plus size={18} />
            Add Attribute
          </button>
        </div>
      </div>

      {Object.keys(attributes).length > 0 && (
        <div className="mt-6 bg-gradient-to-r from-orange-50 to-red-50 border border-orange-200 rounded-xl" style={{ padding: '3%' }}>
          <div className="flex items-center mb-3 text-sm text-gray-600">
            <Settings className="w-4 h-4 mr-2" />
            <strong>Template Usage:</strong> Use these attributes in your system prompt or agent instructions
          </div>
          <div className="space-y-2">
            {Object.entries(attributes).map(([key, value]) => (
              <div key={key} className="text-sm font-mono text-gray-700 bg-white/50 rounded-lg px-3 py-2">
                <span className="text-blue-600 font-medium">{`{{ ${key} }}`}</span>
                <span className="text-gray-500 mx-2">→</span>
                <span className="text-green-600 font-medium">{value}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default GlobalAttributes;