import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import "../components"

Item {
    id: readyPage

    signal backRequested()
    signal finishRequested()

    ColumnLayout {
        anchors.fill: parent
        anchors.leftMargin: 46
        anchors.rightMargin: 46
        anchors.topMargin: 28
        anchors.bottomMargin: 26
        spacing: 16

        Item {
            Layout.fillHeight: true
        }

        Rectangle {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 72
            Layout.preferredHeight: 72
            radius: 24
            color: "#14332F"
            border.width: 1
            border.color: "#245A53"

            Text {
                anchors.centerIn: parent
                text: "✓"
                color: "#20B8AE"
                font.pixelSize: 34
                font.weight: Font.Bold
            }
        }

        Text {
            Layout.fillWidth: true
            text: "KoeScribe is ready"
            color: "#F4F1E8"
            font.pixelSize: 34
            font.weight: Font.Bold
            horizontalAlignment: Text.AlignHCenter
        }

        Text {
            Layout.fillWidth: true
            text: "Your local voice-dictation setup is complete."
            color: "#98A2B3"
            font.pixelSize: 16
            horizontalAlignment: Text.AlignHCenter
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.topMargin: 12
            implicitHeight: summaryColumn.implicitHeight + 34
            radius: 16
            color: "#151B23"
            border.width: 1
            border.color: "#27313D"

            ColumnLayout {
                id: summaryColumn
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                anchors.leftMargin: 20
                anchors.rightMargin: 20
                spacing: 14

                RowLayout {
                    Layout.fillWidth: true
                    Text { text: "Speech model"; color: "#8490A0"; font.pixelSize: 13 }
                    Item { Layout.fillWidth: true }
                    Text {
                        text: setupController.selectedModel.name || "Not selected"
                        color: "#F4F1E8"
                        font.pixelSize: 13
                        font.weight: Font.DemiBold
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: 1
                    color: "#27313D"
                }

                RowLayout {
                    Layout.fillWidth: true
                    Text { text: "LM Studio"; color: "#8490A0"; font.pixelSize: 13 }
                    Item { Layout.fillWidth: true }
                    Text {
                        text: setupController.lmStudioEnabled
                              ? setupController.selectedLmStudioModelId
                              : "Disabled"
                        color: "#F4F1E8"
                        font.pixelSize: 13
                        font.weight: Font.DemiBold
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: 1
                    color: "#27313D"
                }

                RowLayout {
                    Layout.fillWidth: true
                    Text { text: "Microphone"; color: "#8490A0"; font.pixelSize: 13 }
                    Item { Layout.fillWidth: true }
                    Text {
                        Layout.maximumWidth: 360
                        text: microphoneController.selectedMicrophone.name || "Not selected"
                        color: "#F4F1E8"
                        font.pixelSize: 13
                        font.weight: Font.DemiBold
                        elide: Text.ElideRight
                    }
                }
            }
        }

        Text {
            Layout.fillWidth: true
            Layout.topMargin: 8
            text: "These settings are stored locally and can be changed later."
            color: "#667180"
            font.pixelSize: 12
            horizontalAlignment: Text.AlignHCenter
        }

        Item {
            Layout.fillHeight: true
        }

        RowLayout {
            Layout.fillWidth: true

            Button {
                id: backButton
                implicitWidth: 110
                implicitHeight: 48
                text: "Back"
                flat: true
                hoverEnabled: true

                contentItem: Text {
                    text: backButton.text
                    color: backButton.hovered ? "#F4F1E8" : "#98A2B3"
                    font.pixelSize: 14
                    font.weight: Font.DemiBold
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }

                background: Rectangle {
                    radius: 12
                    color: backButton.hovered ? "#1A222C" : "transparent"
                    border.width: 1
                    border.color: "#303A46"
                }

                onClicked: readyPage.backRequested()
            }

            Item {
                Layout.fillWidth: true
            }

            Text {
                text: "Step 5 of 5"
                color: "#667180"
                font.pixelSize: 12
            }

            PrimaryButton {
                text: "Open KoeScribe"
                onClicked: {
                    setupController.finishSetup(
                        microphoneController.selectedMicrophoneId
                    )
                    readyPage.finishRequested()
                }
            }
        }
    }
}
