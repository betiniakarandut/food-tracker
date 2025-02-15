document.addEventListener('DOMContentLoaded', () => {
    const mealTimeSelect = document.getElementById('mealTime');
    const participantIdInput = document.getElementById('participantId');
    const checkButton = document.getElementById('checkButton');
    const resultDiv = document.getElementById('result');
    const errorDiv = document.getElementById('error');
    const mealCountsDiv = document.getElementById('mealCounts');
    const remainingParticipantsButton = document.getElementById("remainingParticipantsButton");
    const remainingParticipantsList = document.getElementById("remainingParticipantsList");

    remainingParticipantsButton.addEventListener("click", () => {
        const mealTime = mealTimeSelect.value;

        fetch(`/meals/remaining_participants/${mealTime}`)
            .then(response => response.json())
            .then(data => {
                remainingParticipantsList.innerHTML = "";
                const sortedParticipants = data.remaining_participants.sort();

                sortedParticipants.forEach(participant => {
                    const li = document.createElement("li");
                    li.textContent = participant;
                    remainingParticipantsList.appendChild(li);
                });
            })
            .catch(error => {
                console.error("Error fetching remaining participants:", error);
                remainingParticipantsList.innerHTML = "<p>Error fetching remaining participants.</p>";
            });
    });


    checkButton.addEventListener('click', () => {
        const mealTime = mealTimeSelect.value;
        const participantId = participantIdInput.value;

        fetch('/meals/serve_food', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ meal_time: mealTime, participant_id: participantId })
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
                getRemainingParticipants(); // Update remaining participants
            })
            .catch(error => {
                resultDiv.textContent = '';
                errorDiv.textContent = error.message;
            });
    });


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

    function getRemainingParticipants() {
        const mealTime = mealTimeSelect.value;

        fetch(`/meals/remaining_participants/${mealTime}`)
            .then(response => response.json())
            .then(data => {
                remainingParticipantsList.innerHTML = "";
                const sortedParticipants = data.remaining_participants.sort();

                sortedParticipants.forEach(participant => {
                    const li = document.createElement("li");
                    li.textContent = participant;
                    remainingParticipantsList.appendChild(li);
                });
            })
            .catch(error => {
                console.error("Error fetching remaining participants:", error);
                remainingParticipantsList.innerHTML = "<p>Error fetching remaining participants.</p>";
            });
    }


    getMealCounts(); // Initial load
    getRemainingParticipants(); // Initial load

});