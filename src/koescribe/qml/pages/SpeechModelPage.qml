import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import "../components"

Item {
    id: speechPage

    signal backRequested()
    signal continueRequested()

    ColumnLayout {
        anchors.fill: parent
        anchors.leftMargin: 46
        anchors.rightMargin: 46
        anchors.topMargin: 28
        anchors.bottomMargin: 26
        spacing: 14

        Text {
            text: "Choose a speech model"
            color: "#F4F1E8"
            font.pixelSize: 32
            font.weight: Font.Bold
        }

        Text {
            Layout.fillWidth: true
            text: "Choose the faster-whisper model that will transcribe your voice locally."
            color: "#98A2B3"
            font.pixelSize: 16
            wrapMode: Text.WordWrap
        }

        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 56
            radius: 12
            color: "#132825"
            border.width: 1
            border.color: "#20564F"

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 16
                anchors.rightMargin: 16
                spacing: 10

                Text {
                    text: "✦"
                    color: "#20B8AE"
                    font.pixelSize: 18
                }

                Text {
                    Layout.fillWidth: true
                    text: "KoeScribe detected your hardware and recommends "
                          + setupController.recommendedModelId + "."
                    color: "#9FE8DF"
                    font.pixelSize: 13
                    wrapMode: Text.WordWrap
                }
            }
        }

        ListView {
            id: modelList
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 10
            clip: true
            model: setupController.whisperModels

            ScrollBar.vertical: ScrollBar {
                policy: ScrollBar.AsNeeded
            }

            delegate: Rectangle {
                id: modelCard

                required property var modelData
                property bool selected: setupController.selectedModelId === modelData.model_id

                width: modelList.width
                height: 112
                radius: 14
                color: selected ? "#192A2B" : "#151B23"
                border.width: selected ? 2 : 1
                border.color: selected ? "#20B8AE" : "#27313D"

                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    enabled: !setupController.downloading

                    onClicked: {
                        setupController.selectWhisperModel(modelCard.modelData.model_id)
                    }
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 14

                    Rectangle {
                        Layout.preferredWidth: 24
                        Layout.preferredHeight: 24
                        radius: 12
                        color: modelCard.selected ? "#20B8AE" : "transparent"
                        border.width: 2
                        border.color: modelCard.selected ? "#20B8AE" : "#536170"

                        Rectangle {
                            visible: modelCard.selected
                            anchors.centerIn: parent
                            width: 8
                            height: 8
                            radius: 4
                            color: "#071311"
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 5

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Text {
                                text: modelCard.modelData.name
                                color: "#F4F1E8"
                                font.pixelSize: 16
                                font.weight: Font.DemiBold
                            }

                            Rectangle {
                                visible: modelCard.modelData.recommended
                                implicitWidth: recommendedText.implicitWidth + 18
                                implicitHeight: 24
                                radius: 12
                                color: "#14332F"

                                Text {
                                    id: recommendedText
                                    anchors.centerIn: parent
                                    text: "Recommended"
                                    color: "#79D8CE"
                                    font.pixelSize: 11
                                    font.weight: Font.DemiBold
                                }
                            }

                            Rectangle {
                                visible: modelCard.modelData.downloaded
                                implicitWidth: downloadedText.implicitWidth + 18
                                implicitHeight: 24
                                radius: 12
                                color: "#202A37"

                                Text {
                                    id: downloadedText
                                    anchors.centerIn: parent
                                    text: "Downloaded"
                                    color: "#B8C2D0"
                                    font.pixelSize: 11
                                    font.weight: Font.DemiBold
                                }
                            }

                            Item {
                                Layout.fillWidth: true
                            }

                            Text {
                                text: modelCard.modelData.download_size
                                color: "#8490A0"
                                font.pixelSize: 12
                            }
                        }

                        Text {
                            Layout.fillWidth: true
                            text: modelCard.modelData.description
                            color: "#98A2B3"
                            font.pixelSize: 13
                            elide: Text.ElideRight
                        }

                        Text {
                            Layout.fillWidth: true
                            text: modelCard.modelData.speed
                                  + " · "
                                  + modelCard.modelData.accuracy
                                  + " accuracy · "
                                  + modelCard.modelData.recommended_vram
                            color: "#697586"
                            font.pixelSize: 12
                        }
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            visible: setupController.selectedModel.recommended === true
            implicitHeight: recommendationText.implicitHeight + 28
            radius: 12
            color: "#111D20"
            border.width: 1
            border.color: "#1E3D3B"

            Text {
                id: recommendationText
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                anchors.leftMargin: 16
                anchors.rightMargin: 16
                text: setupController.selectedModel.recommendation_reason || ""
                color: "#8FCFC8"
                font.pixelSize: 12
                wrapMode: Text.WordWrap
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 12

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

                onClicked: {
                    speechPage.backRequested()
                }
            }

            Item {
                Layout.fillWidth: true
            }

            BusyIndicator {
                Layout.preferredWidth: 28
                Layout.preferredHeight: 28
                visible: setupController.downloading
                running: setupController.downloading
                palette.highlight: "#20B8AE"
            }

            Text {
                visible: setupController.downloadStatus !== ""
                Layout.maximumWidth: 260
                text: setupController.downloadStatus
                color: "#98A2B3"
                font.pixelSize: 12
                elide: Text.ElideRight
            }

            PrimaryButton {
                text: {
                    if (setupController.downloading) {
                        return "Downloading..."
                    }
                    if (setupController.selectedModelDownloaded) {
                        return "Continue"
                    }
                    return "Download model"
                }

                enabled: !setupController.downloading

                onClicked: {
                    if (setupController.selectedModelDownloaded) {
                        speechPage.continueRequested()
                    } else {
                        setupController.downloadSelectedModel()
                    }
                }
            }
        }
    }
}
