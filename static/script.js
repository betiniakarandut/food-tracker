document.addEventListener('DOMContentLoaded', () => {
    const mealTimeSelect = document.getElementById('mealTime');
    const participantIdInput = document.getElementById('participantId');
    const checkButton = document.getElementById('checkButton');
    const resultDiv = document.getElementById('result');
    const errorDiv = document.getElementById('error');
    const mealCountsDiv = document.getElementById('mealCounts');
    const awaitingDiv = document.getElementById('awaitingParticipants');

    const statusMealTimeSelect = document.getElementById('statusMealTime');
    const statusParticipantIdInput = document.getElementById('statusParticipantId');
    const checkStatusButton = document.getElementById('checkStatusButton');
    const statusDiv = document.getElementById('status');

    const remainingParticipantsButton = document.getElementById("remainingParticipantsButton"); // Add this button to your HTML
    const remainingParticipantsList = document.getElementById("remainingParticipantsList"); // Add this list to your HTML


    let eventSource;

    
    remainingParticipantsButton.addEventListener("click", () => {
        const mealTime = mealTimeSelect.value; // Or get it from wherever you need it

        fetch(`/meals/remaining_participants/${mealTime}`)
            .then(response => response.json())
            .then(data => {
                remainingParticipantsList.innerHTML = ""; // Clear existing list
                const sortedParticipants = data.remaining_participants.sort(); // Sort here if needed

                sortedParticipants.forEach(participant => {
                    const li = document.createElement("li");
                    li.textContent = participant;
                    remainingParticipantsList.appendChild(li);
                });
            });
    });


    function displayAwaitingParticipants() {
        if (eventSource) {
            eventSource.close();
        }

        eventSource = new EventSource('/meals/awaiting_participants');

        eventSource.onmessage = (event) => {
            const awaiting = JSON.parse(event.data);
            awaitingDiv.innerHTML = '';

            if (Object.keys(awaiting).length === 0) {
                awaitingDiv.innerHTML = "<p>No participants are currently awaiting service.</p>";
                return;
            }

            for (const participant in awaiting) {
                const { meal_time, expiry_time } = awaiting[participant];
                const listItem = document.createElement('li');
                listItem.textContent = `${participant} - ${meal_time} (Expires: ${new Date(expiry_time).toLocaleString()})`;

                const confirmButton = document.createElement('button');
                confirmButton.textContent = "Confirm Served";
                confirmButton.classList.add('confirm-button');
                confirmButton.dataset.participantId = participant;
                confirmButton.dataset.mealTime = meal_time;
                confirmButton.addEventListener('click', confirmFoodServed);

                listItem.appendChild(confirmButton);
                awaitingDiv.appendChild(listItem);
            }
        };

        eventSource.onerror = (error) => {
            console.error("SSE error:", error);
            awaitingDiv.innerHTML = "<p>Error fetching awaiting list.</p>";
        };
    }

    checkButton.addEventListener('click', () => {
        const mealTime = mealTimeSelect.value;
        const participantId = participantIdInput.value;

        fetch('/meals/serve_food', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ meal_time: mealTime, participant_id: participantId})
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(err.detail || 'Error');
                });
            }
            return response.json();
        })
        .then(data => {
            resultDiv.textContent = data.message;
            errorDiv.textContent = '';
            getMealCounts();
            displayAwaitingParticipants();
        })
        .catch(error => {
            resultDiv.textContent = '';
            errorDiv.textContent = error.message;
        });


    });

    checkStatusButton.addEventListener('click', () => { // Event listener for the Check Status button
        const mealTime = statusMealTimeSelect.value;
        const participantId = statusParticipantIdInput.value;

        fetch(`/meals/participant_status/${participantId}?meal_time=${mealTime}`)
            .then(response => response.json())
            .then(data => {
                statusDiv.textContent = data.message;
            })
            .catch(error => {
                console.error("Error fetching participant status:", error);
                statusDiv.textContent = "Error checking participant status. Please try again.";
            });
    });


    function confirmFoodServed(event) {
        const participantId = event.target.dataset.participantId;
        const mealTime = event.target.dataset.mealTime;

        if (!mealTime || !participantId) {
            console.error("Invalid payload:", {
                meal_time: mealTime,
                participant_id: participantId
            });
            alert("Both meal time and participant ID are required.");
            return;
        }

        const payload = {
            meal_time: mealTime,
            participant_id: participantId
        };

        console.log("Payload for /meals/food_is_served:", payload);

        fetch('/meals/food_is_served', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    console.error("Server error response:", err);
                    throw new Error(err.detail || 'Error occurred while confirming food served.');
                });
            }
            return response.json();
        })
        .then(data => {
            console.log("Server success response:", data);
            resultDiv.textContent = data.message;
            errorDiv.textContent = '';
            getMealCounts();
            displayAwaitingParticipants();
        })
        .catch(error => {
            console.error("Error confirming food served:", error);
            resultDiv.textContent = '';
            errorDiv.textContent = error.message;
        });
    }

    function getMealCounts() {
        const mealTime = mealTimeSelect.value;

        fetch(`/meals/meal_counts?meal_time=${mealTime}`)
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => {
                        throw new Error(err.detail || 'Error');
                    });
                }
                return response.json();
            })
            .then(mealCounts => {
                mealCountsDiv.innerHTML = '';
                for (const mealTime in mealCounts) {
                    const count = mealCounts[mealTime];
                    const p = document.createElement('p');
                    p.textContent = `${mealTime}: ${count}`;
                    mealCountsDiv.appendChild(p);
                }
            })
            .catch(error => {
                console.error("Error fetching meal counts:", error);
                mealCountsDiv.innerHTML = "<p>Error fetching meal counts.</p>";
            });
    }

    getMealCounts();
    displayAwaitingParticipants();
});