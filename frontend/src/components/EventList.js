import React from 'react';

function EventList({ events, temporalDescriptions }) {
  return (
    <div>
      <h2>Events</h2>
      <ul>
        {events && events.map((event, index) => (
          <li key={index}>
            {event.timestamp.toFixed(2)}s: {event.type} - {event.description}
          </li>
        ))}
      </ul>
      <h2>Temporal Descriptions</h2>
      <ul>
        {temporalDescriptions && temporalDescriptions.map((desc, index) => (
          <li key={index}>
            {desc.start_time.toFixed(2)}s - {desc.end_time.toFixed(2)}s: {desc.description}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default EventList;