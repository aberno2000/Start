#include "../include/Geometry/MathVector.hpp"

void MathVector::rotate_y(double beta)
{
    double cosBeta{std::cos(beta)}, sinBeta{std::sin(beta)},
        tempX{cosBeta * x + sinBeta * z},
        tempZ{-sinBeta * x + cosBeta * z};

    x = tempX;
    z = tempZ;
}

void MathVector::rotate_z(double gamma)
{
    double cosGamma{std::cos(gamma)}, sinGamma{std::sin(gamma)},
        tempX{cosGamma * x - sinGamma * y},
        tempY{sinGamma * x + cosGamma * y};

    x = tempX;
    y = tempY;
}

MathVector::MathVector() {}

MathVector::MathVector(double x_, double y_, double z_) : x(x_), y(y_), z(z_) {}

MathVector &MathVector::operator=(double value)
{
    x = value;
    y = value;
    z = value;
    return *this;
}

MathVector MathVector::createCoordinates(double x_, double y_, double z_)
{
    MathVector cords;

    cords.x = x_;
    cords.y = y_;
    cords.z = z_;

    return cords;
}

MathVector MathVector::createRandomVector(double from, double to)
{
    std::random_device rd;
    std::mt19937 gen(rd.entropy() ? rd() : time(nullptr));
    std::uniform_real_distribution<double> dis(from, to);
    return MathVector(dis(gen), dis(gen), dis(gen));
}

void MathVector::setXYZ(double x_, double y_, double z_)
{
    x = x_;
    y = y_;
    z = z_;
}

double MathVector::module() const { return std::sqrt(x * x + y * y + z * z); }

double MathVector::distance(MathVector const &other) const { return std::sqrt(std::pow(other.x - x, 2) +
                                                                              std::pow(other.y - y, 2) +
                                                                              std::pow(other.z - z, 2)); }
double MathVector::distance(MathVector &&other) const { return std::sqrt(std::pow(other.x - x, 2) +
                                                                         std::pow(other.y - y, 2) +
                                                                         std::pow(other.z - z, 2)); }

bool MathVector::isParallel(MathVector const &other) const
{
    double koef{x / other.x};
    return (y == koef * other.y) && (z == koef * other.z);
}
bool MathVector::isParallel(MathVector &&other) const
{
    double koef{x / other.x};
    return (y == koef * other.y) && (z == koef * other.z);
}

bool MathVector::isOrthogonal(MathVector const &other) const { return dotProduct(other) == 0; }
bool MathVector::isOrthogonal(MathVector &&other) const { return dotProduct(std::move(other)) == 0; }

double MathVector::calculateTriangleArea(MathVector const &A,
                                         MathVector const &B,
                                         MathVector const &C)
{
    return std::fabs((B.getX() - A.getX()) * (C.getY() - A.getY()) -
                     (B.getY() - A.getY()) * (C.getX() - A.getX())) /
           2.0;
}
double MathVector::calculateTriangleArea(MathVector &&A,
                                         MathVector &&B,
                                         MathVector &&C)
{
    return std::fabs((B.getX() - A.getX()) * (C.getY() - A.getY()) -
                     (B.getY() - A.getY()) * (C.getX() - A.getX())) /
           2.0;
}

MathVector MathVector::operator-() { return MathVector(-x, -y, -z); }

MathVector MathVector::operator-(MathVector const &other) const { return MathVector(x - other.x, y - other.y, z - other.z); }
MathVector MathVector::operator+(MathVector const &other) const { return MathVector(x + other.x, y + other.y, z + other.z); }

MathVector MathVector::operator-(double value) const { return MathVector(x - value, y - value, z - value); }
MathVector MathVector::operator+(double value) const { return MathVector(x + value, y + value, z + value); }

MathVector &MathVector::operator+=(const MathVector &other)
{
    x += other.x;
    y += other.y;
    z += other.z;
    return *this;
}

MathVector &MathVector::operator-=(const MathVector &other)
{
    x -= other.x;
    y -= other.y;
    z -= other.z;
    return *this;
}

MathVector &MathVector::operator+=(double value)
{
    x += value;
    y += value;
    z += value;
    return *this;
}

MathVector &MathVector::operator-=(double value)
{
    x -= value;
    y -= value;
    z -= value;
    return *this;
}

MathVector MathVector::operator*(double value) const { return MathVector(x * value, y * value, z * value); }
double MathVector::operator*(MathVector const &other) const { return (x * other.x + y * other.y + z * other.z); }
double MathVector::operator*(MathVector &&other) const { return (x * other.x + y * other.y + z * other.z); }
double MathVector::dotProduct(MathVector const &other) const { return (*this) * other; }
double MathVector::dotProduct(MathVector &&other) const { return (*this) * other; }
MathVector MathVector::crossProduct(MathVector const &other) const { return MathVector(y * other.z - z * other.y, z * other.x - x * other.z, x * other.y - y * other.x); }
MathVector MathVector::crossProduct(MathVector &&other) const { return MathVector(y * other.z - z * other.y, z * other.x - x * other.z, x * other.y - y * other.x); }

MathVector MathVector::operator/(double value) const
{
    if (value == 0)
        throw std::overflow_error("Division by null: Elements of vector can't be divided by 0");
    return MathVector(x / value, y / value, z / value);
}

std::pair<double, double> MathVector::calcBetaGamma() const
{
    double magnitude{module()};
    if (magnitude == 0)
        throw std::runtime_error("Cannot calculate angles for a zero vector.");

    // Calculating rotation angles
    double beta{acos(getZ() / magnitude)},
        gamma{atan2(getY(), getX())};
    return std::make_pair(beta, gamma);
}

void MathVector::rotation(double beta, double gamma)
{
    rotate_y(beta);
    rotate_z(gamma);
}
void MathVector::rotation(std::pair<double, double> const &p) { rotation(p.first, p.second); }
void MathVector::rotation(std::pair<double, double> &&p) noexcept { rotation(p.first, p.second); }

MathVector MathVector::sign() const noexcept { return MathVector(util::signFunc(x), util::signFunc(y), util::signFunc(z)); }
