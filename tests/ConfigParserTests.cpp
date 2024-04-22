#include <filesystem>
#include <fstream>
#include <gtest/gtest.h>
#include <nlohmann/json.hpp>

#include "../include/Utilities/ConfigParser.hpp"

using json = nlohmann::json;

static std::string configPath{"../configs/test_config.json"};
class ConfigParserTest : public ::testing::Test
{
protected:
    void SetUp() override
    {
        std::filesystem::path dirPath{std::filesystem::path(configPath).parent_path()};
        if (!std::filesystem::exists(dirPath))
            if (!std::filesystem::create_directories(dirPath))
                throw std::runtime_error("Failed to create directory: " + dirPath.string());

        std::ofstream outFile(configPath, std::ios::out | std::ios::trunc);
        if (!outFile)
            throw std::runtime_error("Failed to open file for writing: " + configPath);

        json j;
        j["Mesh File"] = configPath;
        j["Count"] = 1000;
        j["Threads"] = 4;
        j["Time Step"] = 0.01;
        j["Simulation Time"] = 1.0;
        j["T"] = 300.0;
        j["P"] = 101325;
        j["V"] = 1.0;
        j["Particles"] = json::array({"Au", "Ne"});
        j["Energy"] = 1500.0;
        j["Model"] = "VHS";

        outFile << j.dump(4);
        outFile.close();
    }

    void TearDown() override
    {
        if (!std::filesystem::remove(configPath))
            std::cerr << "Failed to delete temporary config file: " + configPath << std::endl;
    }
};

TEST_F(ConfigParserTest, ValidConfiguration)
{
    ConfigParser config(configPath);
    EXPECT_TRUE(config.isValid());

    EXPECT_EQ(config.getNumThreads(), 4);
    EXPECT_EQ(config.getParticlesCount(), 1000);
    EXPECT_DOUBLE_EQ(config.getTimeStep(), 0.01);
    EXPECT_DOUBLE_EQ(config.getSimulationTime(), 1.0);
    EXPECT_DOUBLE_EQ(config.getTemperature(), 300);
    EXPECT_DOUBLE_EQ(config.getPressure(), 101325);
    EXPECT_DOUBLE_EQ(config.getVolume(), 1.0);
    EXPECT_DOUBLE_EQ(config.getEnergy(), 1500);
    EXPECT_EQ(config.getScatteringModel(), "VHS");
    EXPECT_EQ(config.getProjective(), ParticleType::Au);
    EXPECT_EQ(config.getGas(), ParticleType::Ne);
}

TEST_F(ConfigParserTest, ValidConfigurations)
{
    for (int i{1}; i <= 10; ++i)
    {
        std::string configFile("../configs/config_valid_" + std::to_string(i) + ".json.gtest");
        std::ifstream file(configFile);
        if (!file.is_open())
            FAIL() << "Could not open file: " << configFile;

        std::string content((std::istreambuf_iterator<char>(file)), std::istreambuf_iterator<char>());
        if (content.empty())
            FAIL() << "File is empty: " << configFile;

        ConfigParser configParser(configFile);
        EXPECT_EQ(configParser.getStatusCode(), STATUS_OK) << "Failed on valid config file: " << configFile;
    }
}

TEST_F(ConfigParserTest, InvalidConfigurations)
{
    for (int i{1}; i <= 10; ++i)
    {
        std::string configFile("../configs/config_invalid_" + std::to_string(i) + ".json.gtest");
        std::ifstream file(configFile);
        if (!file.is_open())
            FAIL() << "Could not open file: " << configFile;

        std::string content((std::istreambuf_iterator<char>(file)), std::istreambuf_iterator<char>());
        if (content.empty())
            FAIL() << "File is empty: " << configFile;

        ConfigParser configParser(configFile);
        EXPECT_FALSE(configParser.isValid()) << "Configuration should be invalid for file: " << configFile;
        EXPECT_NE(configParser.getStatusCode(), STATUS_OK) << "Status should not be OK for invalid config file: " << configFile;
    }
}
