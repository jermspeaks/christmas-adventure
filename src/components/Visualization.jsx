import { useState, useEffect, useRef } from 'preact/hooks';
import dagre from 'dagre';

export function Visualization() {
  const [gameData, setGameData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [nodePositions, setNodePositions] = useState(new Map());
  const [connections, setConnections] = useState([]);
  const [svgDimensions, setSvgDimensions] = useState({ width: 800, height: 600 });
  const containerRef = useRef(null);
  const graphRef = useRef(null);
  const nodeRefs = useRef(new Map());

  useEffect(() => {
    fetch('/game-data.json')
      .then(res => {
        if (!res.ok) {
          throw new Error(`Failed to load game data: ${res.statusText}`);
        }
        return res.json();
      })
      .then(data => {
        setGameData(data.gameData);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="loading">
        <p>Loading visualization...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error">
        <h1>Error</h1>
        <p>{error}</p>
      </div>
    );
  }

  if (!gameData) {
    return (
      <div className="error">
        <h1>Error</h1>
        <p>No game data available.</p>
      </div>
    );
  }

  // Build graph structure
  const sections = Object.values(gameData);
  const sectionMap = new Map(sections.map(s => [s.id, s]));

  // Build edges (connections) from choices
  const buildEdges = () => {
    const edges = [];
    sections.forEach(section => {
      if (section.choices) {
        section.choices.forEach((choice, idx) => {
          if (choice.target && sectionMap.has(choice.target)) {
            edges.push({
              id: `${section.id}-${choice.target}-${idx}`,
              from: section.id,
              to: choice.target,
              choiceIndex: idx,
            });
          }
        });
      }
    });
    return edges;
  };

  const edges = buildEdges();

  // Layered graph layout using dagre
  useEffect(() => {
    if (!gameData || !graphRef.current) return;

    // Build graph structure for dagre
    const g = new dagre.graphlib.Graph();
    g.setGraph({
      rankdir: 'TB', // Top to bottom
      nodesep: 60,   // Minimum horizontal spacing between nodes (reduced for more compact layout)
      ranksep: 200,  // Minimum vertical spacing between layers
      marginx: 30,
      marginy: 50,
    });
    g.setDefaultEdgeLabel(() => ({}));

    // Add nodes to graph
    sections.forEach(section => {
      // Estimate node size (will be updated after rendering)
      g.setNode(section.id, {
        width: 220,  // max-width from CSS
        height: 150, // estimated height
        label: section.title,
      });
    });

    // Add edges to graph
    edges.forEach(edge => {
      g.setEdge(edge.from, edge.to, {
        id: edge.id,
        choiceIndex: edge.choiceIndex,
      });
    });

    // Run dagre layout
    dagre.layout(g);

    // Extract positions from dagre
    const positions = new Map();
    let maxX = 0;
    let maxY = 0;

    g.nodes().forEach(nodeId => {
      const node = g.node(nodeId);
      positions.set(nodeId, {
        x: node.x,
        y: node.y,
      });
      maxX = Math.max(maxX, node.x + node.width / 2);
      maxY = Math.max(maxY, node.y + node.height / 2);
    });

    // Update SVG dimensions based on graph bounds
    const padding = 50;
    setSvgDimensions({
      width: Math.max(600, maxX + padding),
      height: Math.max(600, maxY + padding),
    });

    // Set node positions
    setNodePositions(positions);

    // After nodes are rendered, update with actual dimensions and recalculate
    const updateWithActualDimensions = () => {
      // Get actual node dimensions
      const actualDimensions = new Map();
      let hasAllDimensions = true;

      sections.forEach(section => {
        const nodeEl = nodeRefs.current.get(section.id);
        if (nodeEl) {
          actualDimensions.set(section.id, {
            width: nodeEl.offsetWidth || 220,
            height: nodeEl.offsetHeight || 150,
          });
        } else {
          hasAllDimensions = false;
        }
      });

      if (!hasAllDimensions) {
        // Retry after a short delay
        setTimeout(updateWithActualDimensions, 50);
        return;
      }

      // Rebuild graph with actual dimensions
      const g2 = new dagre.graphlib.Graph();
      g2.setGraph({
        rankdir: 'TB',
        nodesep: 60,   // Minimum horizontal spacing between nodes (reduced for more compact layout)
        ranksep: 200,
        marginx: 30,
        marginy: 50,
      });
      g2.setDefaultEdgeLabel(() => ({}));

      sections.forEach(section => {
        const dims = actualDimensions.get(section.id);
        g2.setNode(section.id, {
          width: dims.width,
          height: dims.height,
          label: section.title,
        });
      });

      edges.forEach(edge => {
        g2.setEdge(edge.from, edge.to, {
          id: edge.id,
          choiceIndex: edge.choiceIndex,
        });
      });

      dagre.layout(g2);

      const positions2 = new Map();
      let maxX2 = 0;
      let maxY2 = 0;

      g2.nodes().forEach(nodeId => {
        const node = g2.node(nodeId);
        positions2.set(nodeId, {
          x: node.x,
          y: node.y,
        });
        maxX2 = Math.max(maxX2, node.x + node.width / 2);
        maxY2 = Math.max(maxY2, node.y + node.height / 2);
      });

      const padding2 = 50;
      setSvgDimensions({
        width: Math.max(600, maxX2 + padding2),
        height: Math.max(600, maxY2 + padding2),
      });

      setNodePositions(positions2);
    };

    // Wait a bit for initial render, then update with actual dimensions
    setTimeout(updateWithActualDimensions, 100);
  }, [gameData, edges, sections]);

  // Calculate connection paths after positions are set
  useEffect(() => {
    if (nodePositions.size === 0) return;

    const newConnections = [];

    edges.forEach(edge => {
      const fromPos = nodePositions.get(edge.from);
      const toPos = nodePositions.get(edge.to);
      if (!fromPos || !toPos) return;

      // Get actual node dimensions for connection points
      const fromNode = nodeRefs.current.get(edge.from);
      const toNode = nodeRefs.current.get(edge.to);
      if (!fromNode || !toNode) return;

      // Use node dimensions directly (nodes are centered on their positions)
      const fromHeight = fromNode.offsetHeight || 100;
      const toHeight = toNode.offsetHeight || 100;

      // Calculate connection points (bottom of from node, top of to node)
      const fromX = fromPos.x;
      const fromY = fromPos.y + fromHeight / 2;
      const toX = toPos.x;
      const toY = toPos.y - toHeight / 2;

      // Calculate control points for smooth curve
      const dx = toX - fromX;
      const dy = toY - fromY;
      const distance = Math.sqrt(dx * dx + dy * dy);
      const controlOffset = Math.max(30, distance * 0.2);
      const controlY1 = fromY + controlOffset;
      const controlY2 = toY - controlOffset;

      newConnections.push({
        id: edge.id,
        fromX,
        fromY,
        toX,
        toY,
        controlY1,
        controlY2,
      });
    });

    setConnections(newConnections);
  }, [nodePositions, edges]);

  return (
    <div className="visualization-container" ref={containerRef}>
      <h1>Story Path Map</h1>
      <div 
        className="visualization-graph" 
        ref={graphRef}
        style={{ 
          position: 'relative', 
          width: svgDimensions.width, 
          height: svgDimensions.height,
          margin: '0 auto',
          overflow: 'visible'
        }}
      >
        {/* SVG overlay for connections */}
        {svgDimensions.width > 0 && svgDimensions.height > 0 && (
          <svg 
            className="connection-lines" 
            style={{ 
              position: 'absolute', 
              top: 0, 
              left: 0, 
              width: svgDimensions.width, 
              height: svgDimensions.height, 
              pointerEvents: 'none', 
              zIndex: 0,
              overflow: 'visible'
            }}
            viewBox={`0 0 ${svgDimensions.width} ${svgDimensions.height}`}
            preserveAspectRatio="none"
          >
            <defs>
              <marker
                id="arrowhead"
                markerWidth="40"
                markerHeight="40"
                refX="35"
                refY="10"
                orient="auto"
                markerUnits="userSpaceOnUse"
              >
                <polygon points="0 0, 40 10, 0 20" fill="#c41e3a" stroke="#c41e3a" strokeWidth="2" />
              </marker>
            </defs>
            {connections.map(conn => (
              <path
                key={conn.id}
                d={`M ${conn.fromX} ${conn.fromY} C ${conn.fromX} ${conn.controlY1}, ${conn.toX} ${conn.controlY2}, ${conn.toX} ${conn.toY}`}
                stroke="#c41e3a"
                strokeWidth="2"
                fill="none"
                opacity="0.6"
                marker-end="url(#arrowhead)"
              />
            ))}
          </svg>
        )}

        {/* Graph nodes */}
        <div className="graph-nodes-wrapper" style={{ position: 'relative', zIndex: 1 }}>
          {sections.map(section => {
            const position = nodePositions.get(section.id);
            if (!position) return null;

            return (
              <div
                key={section.id}
                className="graph-node"
                data-section-id={section.id}
                style={{
                  position: 'absolute',
                  left: `${position.x}px`,
                  top: `${position.y}px`,
                  transform: 'translate(-50%, -50%)',
                }}
                ref={el => {
                  if (el) {
                    nodeRefs.current.set(section.id, el);
                  } else {
                    nodeRefs.current.delete(section.id);
                  }
                }}
              >
                <div className="node-content">
                  <h3 className="node-title">{section.title}</h3>
                  {section.choices && section.choices.length > 0 ? (
                    <ul className="node-choices">
                      {section.choices.map((choice, idx) => (
                        <li key={idx} className="node-choice">
                          {choice.text}
                          {choice.target && (
                            <span className="choice-target"> → {sectionMap.get(choice.target)?.title || choice.target}</span>
                          )}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <div className="node-end">The End</div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

