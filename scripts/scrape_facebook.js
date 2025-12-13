#!/usr/bin/env bun
/**
 * Facebook Event Scraper
 *
 * JSON stdin/stdout contract for subprocess communication with Python.
 *
 * Input:  { "action": "scrape_page_events" | "scrape_single_event", "url": "...", "options": {...} }
 * Output: { "success": true, "data": [...] } or { "success": false, "error": "..." }
 */

import {
  scrapeFbEvent,
  scrapeFbEventList,
  EventType,
} from "facebook-event-scraper";

/**
 * Scrape all events from a Facebook page's events listing
 */
async function scrapePageEvents(url, options = {}) {
  const events = [];

  try {
    // Use scrapeFbEventList for page events
    const eventList = await scrapeFbEventList(url, EventType.Upcoming);

    if (!eventList || eventList.length === 0) {
      return [];
    }

    // Limit number of events
    const limit = options.limit || 20;
    const eventsToProcess = eventList.slice(0, limit);

    for (const eventData of eventsToProcess) {
      events.push(normalizeEvent(eventData, url));
    }

    return events;
  } catch (error) {
    throw new Error(`Failed to scrape page events: ${error.message}`);
  }
}

/**
 * Scrape a single Facebook event
 */
async function scrapeSingleEvent(url) {
  try {
    const event = await scrapeFbEvent(url);

    if (!event) {
      throw new Error("Event not found or is private");
    }

    return normalizeEvent(event, url);
  } catch (error) {
    throw new Error(`Failed to scrape event: ${error.message}`);
  }
}

/**
 * Normalize event data to match our Event schema
 */
function normalizeEvent(fbEvent, sourceUrl) {
  // Parse date/time from Facebook's format
  // The library returns startTimestamp as Unix timestamp in seconds
  const startDate = fbEvent.startTimestamp
    ? new Date(fbEvent.startTimestamp * 1000)
    : null;
  const endDate = fbEvent.endTimestamp
    ? new Date(fbEvent.endTimestamp * 1000)
    : null;

  // Extract venue information
  const venue = {};
  if (fbEvent.location) {
    venue.name = fbEvent.location.name || null;
    venue.address = fbEvent.location.address || null;
    venue.city = fbEvent.location.city || null;

    if (fbEvent.location.latitude && fbEvent.location.longitude) {
      venue.coordinates = [
        fbEvent.location.latitude,
        fbEvent.location.longitude,
      ];
    }
  }

  // Build source URL from event ID if not provided
  const eventSourceUrl =
    sourceUrl || `https://www.facebook.com/events/${fbEvent.id}`;

  return {
    title: fbEvent.name || "Untitled Event",
    description: fbEvent.description || null,
    event_date: startDate ? formatDate(startDate) : null,
    start_time: startDate ? formatTime(startDate) : null,
    end_time: endDate ? formatTime(endDate) : null,
    venue: Object.keys(venue).length > 0 ? venue : null,
    ticket_url: fbEvent.ticketUrl || null,
    image_url: fbEvent.photo || null,
    source: "facebook",
    source_url: eventSourceUrl,
    source_id: fbEvent.id || null,
    hosts: fbEvent.hosts || [],
    going_count: fbEvent.usersGoing || null,
    interested_count: fbEvent.usersInterested || null,
  };
}

/**
 * Format date as YYYY-MM-DD
 */
function formatDate(date) {
  return date.toISOString().split("T")[0];
}

/**
 * Format time as HH:MM (24-hour)
 */
function formatTime(date) {
  return date.toTimeString().slice(0, 5);
}

/**
 * Main entry point - read JSON from stdin, write result to stdout
 */
async function main() {
  let input = "";

  // Read all input from stdin
  for await (const chunk of Bun.stdin.stream()) {
    input += new TextDecoder().decode(chunk);
  }

  let request;
  try {
    request = JSON.parse(input);
  } catch (error) {
    console.log(
      JSON.stringify({
        success: false,
        error: `Invalid JSON input: ${error.message}`,
      })
    );
    process.exit(1);
  }

  const { action, url, options = {} } = request;

  if (!action) {
    console.log(
      JSON.stringify({
        success: false,
        error: 'Missing required field: "action"',
      })
    );
    process.exit(1);
  }

  if (!url) {
    console.log(
      JSON.stringify({
        success: false,
        error: 'Missing required field: "url"',
      })
    );
    process.exit(1);
  }

  try {
    let data;

    switch (action) {
      case "scrape_page_events":
        data = await scrapePageEvents(url, options);
        break;

      case "scrape_single_event":
        data = await scrapeSingleEvent(url);
        break;

      default:
        console.log(
          JSON.stringify({
            success: false,
            error: `Unknown action: ${action}`,
          })
        );
        process.exit(1);
    }

    console.log(
      JSON.stringify({
        success: true,
        data: data,
      })
    );
  } catch (error) {
    console.log(
      JSON.stringify({
        success: false,
        error: error.message,
      })
    );
    process.exit(1);
  }
}

main();
