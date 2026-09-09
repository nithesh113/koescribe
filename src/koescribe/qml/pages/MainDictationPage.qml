import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: dictationPage

    signal settingsRequested()

    readonly property string stateTitle:
        dictationController.status
    readonly property string stateDescription:
        dictationController.message

    function toggleRecording() {
        if (dictationController.recording) {
            dictationController.stopRecording()
            return
        }

        dictationController.startRecording(
            microphoneController.selectedMicrophoneId
        )
    }

    function copyTranscription() {
        if (dictationController.transcriptionText === "")
            return

        transcriptArea.forceActiveFocus()
        transcriptArea.selectAll()
        transcriptArea.copy()
        transcriptArea.deselect()
    }

    ScrollView {
        anchors.fill: parent
        clip: true
        contentWidth: availableWidth

        ColumnLayout {
            width: Math.min(820, dictationPage.width - 80)
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 18

            Item { Layout.preferredHeight: 18 }

            RowLayout {
                Layout.fillWidth: true

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 5

                    Text {
                        text: "Dictation"
                        color: "#F4F1E8"
                        font.pixelSize: 30
                        font.weight: Font.Bold
                    }

                    Text {
                        text: "Private voice-to-text, processed on this computer."
                        color: "#8490A0"
                        font.pixelSize: 14
                    }
                }

                Button {
                    id: settingsButton
                    implicitWidth: 108
                    implicitHeight: 42
                    text: "Settings"
                    hoverEnabled: true

                    contentItem: Text {
                        text: settingsButton.text
                        color: settingsButton.hovered ? "#F4F1E8" : "#AAB2C0"
                        font.pixelSize: 13
                        font.weight: Font.DemiBold
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }

                    background: Rectangle {
                        radius: 12
                        color: settingsButton.hovered ? "#1A222C" : "#151B23"
                        border.width: 1
                        border.color: "#303A46"
                    }

                    onClicked: {
                        if (dictationController.recording)
                            dictationController.cancelRecording()
                        dictationPage.settingsRequested()
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                implicitHeight: 300
                radius: 20
                color: "#121920"
                border.width: 1
                border.color: dictationController.recording
                              ? "#27736A"
                              : "#25303B"

                ColumnLayout {
                    anchors.centerIn: parent
                    width: Math.min(520, parent.width - 48)
                    spacing: 13

                    Button {
                        id: recordButton
                        Layout.alignment: Qt.AlignHCenter
                        implicitWidth: 112
                        implicitHeight: 112
                        hoverEnabled: true
                        enabled: !dictationController.transcribing

                        contentItem: Item {
                            BusyIndicator {
                                anchors.centerIn: parent
                                width: 42
                                height: 42
                                visible: dictationController.transcribing
                                running: dictationController.transcribing
                                palette.highlight: "#071311"
                            }

                            Rectangle {
                                visible: !dictationController.transcribing
                                anchors.centerIn: parent
                                width: dictationController.recording ? 28 : 30
                                height: dictationController.recording ? 28 : 38
                                radius: dictationController.recording ? 6 : 15
                                color: dictationController.recording
                                       ? "#F4F1E8"
                                       : "#071311"

                                Rectangle {
                                    visible: !dictationController.recording
                                    width: 13
                                    height: 8
                                    radius: 4
                                    color: "#071311"
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    anchors.top: parent.bottom
                                    anchors.topMargin: 3
                                }
                            }
                        }

                        background: Rectangle {
                            radius: 56
                            color: dictationController.transcribing
                                   ? "#5C837E"
                                   : dictationController.recording
                                   ? (recordButton.hovered ? "#D35F5F" : "#C55252")
                                   : (recordButton.hovered ? "#3ACBC0" : "#20B8AE")
                            border.width: 6
                            border.color: dictationController.recording
                                          ? "#40252A"
                                          : "#16312E"

                            Behavior on color {
                                ColorAnimation { duration: 140 }
                            }
                        }

                        onClicked: dictationPage.toggleRecording()
                    }

                    Text {
                        Layout.fillWidth: true
                        text: dictationPage.stateTitle
                        color: "#F4F1E8"
                        font.pixelSize: 22
                        font.weight: Font.Bold
                        horizontalAlignment: Text.AlignHCenter
                    }

                    Text {
                        Layout.fillWidth: true
                        text: dictationPage.stateDescription
                        color: "#8490A0"
                        font.pixelSize: 13
                        horizontalAlignment: Text.AlignHCenter
                        wrapMode: Text.WordWrap
                    }

                    Text {
                        visible: dictationController.errorMessage !== ""
                        Layout.fillWidth: true
                        text: dictationController.errorMessage
                        color: "#E88787"
                        font.pixelSize: 12
                        horizontalAlignment: Text.AlignHCenter
                        wrapMode: Text.WordWrap
                    }

                    Text {
                        visible: dictationController.recording
                        Layout.fillWidth: true
                        text: dictationController.elapsedText
                        color: "#79D8CE"
                        font.pixelSize: 18
                        font.weight: Font.DemiBold
                        horizontalAlignment: Text.AlignHCenter
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                StatusTile {
                    Layout.fillWidth: true
                    tileLabel: "Speech model"
                    tileValue: setupController.selectedModel.name || "Not selected"
                    indicatorColor: "#20B8AE"
                }

                StatusTile {
                    Layout.fillWidth: true
                    tileLabel: "Acceleration"
                    tileValue: cudaController.ready ? "NVIDIA CUDA" : "CPU fallback"
                    indicatorColor: cudaController.ready ? "#20B8AE" : "#C7A96B"
                }

                StatusTile {
                    Layout.fillWidth: true
                    tileLabel: "LM Studio"
                    tileValue: setupController.lmStudioEnabled
                               ? setupController.selectedLmStudioModelId
                               : "Disabled"
                    indicatorColor: setupController.lmStudioEnabled
                                    ? "#20B8AE"
                                    : "#667180"
                }
            }

            Rectangle {
                Layout.fillWidth: true
                implicitHeight: 190
                radius: 16
                color: "#151B23"
                border.width: 1
                border.color: "#27313D"

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 18
                    spacing: 10

                    RowLayout {
                        Layout.fillWidth: true

                        Text {
                            Layout.fillWidth: true
                            text: "Latest transcription"
                            color: "#F4F1E8"
                            font.pixelSize: 15
                            font.weight: Font.DemiBold
                        }

                        ToolButton {
                            id: copyButton
                            enabled: dictationController.transcriptionText !== ""
                            text: "Copy"
                            onClicked: dictationPage.copyTranscription()
                        }

                        ToolButton {
                            enabled: dictationController.transcriptionText !== ""
                            text: "Clear"
                            onClicked: dictationController.clearTranscription()
                        }
                    }

                    TextArea {
                        id: transcriptArea
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        readOnly: true
                        selectByMouse: true
                        wrapMode: TextEdit.Wrap
                        text: dictationController.transcriptionText
                        placeholderText: "Your transcription will appear here."
                        color: "#D9DEE7"
                        placeholderTextColor: "#596473"
                        font.pixelSize: 14

                        background: Rectangle {
                            radius: 10
                            color: "#10151C"
                            border.width: 1
                            border.color: transcriptArea.activeFocus
                                          ? "#20564F"
                                          : "#222C37"
                        }
                    }
                }
            }

            Text {
                Layout.fillWidth: true
                Layout.bottomMargin: 22
                text: dictationController.recording
                      ? "Recording locally—audio has not left your computer."
                      : dictationController.transcribing
                        ? "Transcribing locally. The interface remains responsive."
                      : "Microphone: "
                        + (microphoneController.selectedMicrophone.name
                           || "Default input")
                color: "#667180"
                font.pixelSize: 12
                horizontalAlignment: Text.AlignHCenter
                elide: Text.ElideRight
            }
        }
    }

    component StatusTile: Rectangle {
        id: statusTile

        property string tileLabel: ""
        property string tileValue: ""
        property color indicatorColor: "#20B8AE"

        implicitHeight: 76
        radius: 14
        color: "#151B23"
        border.width: 1
        border.color: "#27313D"

        RowLayout {
            anchors.fill: parent
            anchors.margins: 14
            spacing: 10

            Rectangle {
                Layout.preferredWidth: 8
                Layout.preferredHeight: 8
                radius: 4
                color: statusTile.indicatorColor
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4

                Text {
                    Layout.fillWidth: true
                    text: statusTile.tileLabel
                    color: "#667180"
                    font.pixelSize: 11
                }

                Text {
                    Layout.fillWidth: true
                    text: statusTile.tileValue
                    color: "#D9DEE7"
                    font.pixelSize: 13
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
                }
            }
        }
    }
}
